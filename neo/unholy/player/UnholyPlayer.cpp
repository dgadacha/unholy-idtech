/*
===========================================================================

UNHOLY -- code de jeu. GPL-3.0, comme le moteur RBDOOM-3-BFG auquel il est lie.

===========================================================================
*/

#include "precompiled.h"
#pragma hdrstop

#include "d3xp/Game_local.h"
#include "player/UnholyPlayer.h"

/*
	Les regles de deplacement propres a UNHOLY portent le prefixe pm_ comme
	celles du moteur : la declaration du personnage les fixe toutes de la meme
	facon, et on les essaie a la console de la meme facon. A leur valeur par
	defaut, elles laissent faire le moteur.
*/
idCVar pm_jumpdelay( "pm_jumpdelay", "0", CVAR_GAME | CVAR_NETWORKSYNC | CVAR_INTEGER,
					 "UNHOLY: millisecondes au sol apres une reception avant de pouvoir ressauter, bouton relache (0 : comme le moteur)" );
idCVar pm_landspeedscale( "pm_landspeedscale", "1", CVAR_GAME | CVAR_NETWORKSYNC | CVAR_FLOAT,
						  "UNHOLY: part de la vitesse horizontale gardee a la reception d'un saut ou d'une chute" );
idCVar pm_sprintforwardonly( "pm_sprintforwardonly", "0", CVAR_GAME | CVAR_NETWORKSYNC | CVAR_BOOL,
							 "UNHOLY: ne courir qu'en avancant" );

idCVar unholy_showMove( "unholy_showMove", "0", CVAR_GAME | CVAR_BOOL, "UNHOLY: affiche le releve du deplacement" );
idCVar unholy_logMove( "unholy_logMove", "0", CVAR_GAME | CVAR_BOOL, "UNHOLY: imprime le deplacement du joueur a chaque image" );
idCVar unholy_moveTest( "unholy_moveTest", "", CVAR_GAME,
						"UNHOLY: lance un scenario du banc d'essai du deplacement (un nom inconnu les liste)" );

// Un pouce en metres : les unites du moteur sont des pouces.
static const float METERS_PER_UNIT = 0.0254f;

CLASS_DECLARATION( idPlayer, UnholyPlayer )
END_CLASS

/*
==============
UnholyPlayer::UnholyPlayer
==============
*/
UnholyPlayer::UnholyPlayer()
{
	jumpReadyTime = 0;
	jumpLatched = false;
	runAtTakeoff = false;
	aiming = false;
	testYaw = 0.0f;
}

/*
==============
UnholyPlayer::Spawn
==============
*/
void UnholyPlayer::Spawn()
{
	ApplyMovementTuning();

	// idPlayer::Spawn a deja pose la boite de collision et la hauteur des yeux
	// avec les valeurs d'avant : on les reprend avec celles du personnage.
	SetClipModel();
	SetEyeHeight( pm_normalviewheight.GetFloat() );
	stamina = pm_stamina.GetFloat();
}

/*
==============
UnholyPlayer::Save
==============
*/
void UnholyPlayer::Save( idSaveGame* savefile ) const
{
	savefile->WriteInt( jumpReadyTime );
	savefile->WriteBool( jumpLatched );
	savefile->WriteBool( runAtTakeoff );
}

/*
==============
UnholyPlayer::Restore
==============
*/
void UnholyPlayer::Restore( idRestoreGame* savefile )
{
	savefile->ReadInt( jumpReadyTime );
	savefile->ReadBool( jumpLatched );
	savefile->ReadBool( runAtTakeoff );

	ApplyMovementTuning();
}

/*
==============
UnholyPlayer::PlayerPhysics
==============
*/
idPhysics_Player* UnholyPlayer::PlayerPhysics() const
{
	return static_cast<idPhysics_Player*>( const_cast<UnholyPlayer*>( this )->GetPlayerPhysics() );
}

/*
==============
UnholyPlayer::ApplyMovementTuning

Chaque cle pm_ de la declaration regle la variable du meme nom. Une cle qui
ne correspond a rien est signalee : c'est presque toujours une faute de frappe,
et une valeur qui ne s'applique pas se cherche longtemps.
==============
*/
void UnholyPlayer::ApplyMovementTuning()
{
	for( const idKeyValue* kv = spawnArgs.MatchPrefix( "pm_" ); kv != NULL; kv = spawnArgs.MatchPrefix( "pm_", kv ) )
	{
		if( cvarSystem->Find( kv->GetKey() ) == NULL )
		{
			gameLocal.Warning( "%s : la cle '%s' ne correspond a aucune variable", spawnArgs.GetString( "classname" ), kv->GetKey().c_str() );
			continue;
		}
		cvarSystem->SetCVarString( kv->GetKey(), kv->GetValue() );
	}
}

/*
==============
UnholyPlayer::Think
==============
*/
void UnholyPlayer::Think()
{
	idPhysics_Player* physics = PlayerPhysics();
	const bool onGround = physics->HasGroundContacts();
	const idVec3 velocity = physics->GetLinearVelocity();

	RunMoveTest();
	ApplyMovementRules( onGround );
	UpdateWeaponScript();

	idPlayer::Think();

	if( !onGround && physics->HasGroundContacts() )
	{
		Landed( velocity );
	}

	MeasureMoveTest();
	if( unholy_logMove.GetBool() )
	{
		LogMovement();
	}
}

/*
==============
UnholyPlayer::ApplyMovementRules

Les commandes du joueur passent par ici avant d'atteindre le moteur.
`onGround` est l'etat au debut de l'image, avant la physique.
==============
*/
void UnholyPlayer::ApplyMovementRules( bool onGround )
{
	// Course : vers l'avant seulement, et jamais en tirant ni en epaulant. Et
	// l'allure prise au decollage tient jusqu'a la reception : on ne se relance
	// pas en l'air.
	if( pm_sprintforwardonly.GetBool() && usercmd.forwardmove <= 0 )
	{
		usercmd.buttons &= ~BUTTON_RUN;
	}
	if( usercmd.buttons & ( BUTTON_ATTACK | BUTTON_ZOOM ) )
	{
		usercmd.buttons &= ~BUTTON_RUN;
	}
	if( onGround )
	{
		runAtTakeoff = ( usercmd.buttons & BUTTON_RUN ) != 0;
	}
	else if( runAtTakeoff )
	{
		usercmd.buttons |= BUTTON_RUN;
	}
	else
	{
		usercmd.buttons &= ~BUTTON_RUN;
	}

	if( pm_jumpdelay.GetInteger() <= 0 )
	{
		return;
	}

	/*
		Saut : seulement depuis le sol, une fois le delai passe, et d'un appui
		franc. Un appui donne en l'air ou pendant le delai est perdu, et il faut
		relacher le bouton pour que le suivant compte.

		Le moteur, lui, laisse ressauter a l'image meme de la reception, sans
		frottement au sol entre les deux : c'est tout le bunny hop. Et l'image
		de la reception commence encore en l'air, ce qui prend aussi l'appui
		donne pile au bon moment.
	*/
	const bool jumpDown = ( usercmd.buttons & BUTTON_JUMP ) != 0;
	const bool jumpAllowed = onGround && gameLocal.time >= jumpReadyTime;
	if( jumpDown && ( jumpLatched || !jumpAllowed ) )
	{
		usercmd.buttons &= ~BUTTON_JUMP;
		jumpLatched = true;
	}
	else if( !jumpDown )
	{
		jumpLatched = false;
	}
}

/*
==============
UnholyPlayer::Landed

Appele a l'image ou le joueur retrouve le sol, avec sa vitesse d'avant.
==============
*/
void UnholyPlayer::Landed( const idVec3& velocityBeforeLanding )
{
	idPhysics_Player* physics = PlayerPhysics();
	const idVec3& down = physics->GetGravityNormal();
	const float impact = velocityBeforeLanding * down;

	// Une marche descendue ne compte pas : seule pese une chute d'au moins une
	// hauteur de marche, ou un saut, qui retombe au moins aussi vite.
	const float stepImpact = idMath::Sqrt( 2.0f * physics->GetGravity().Length() * pm_stepsize.GetFloat() );
	if( impact < stepImpact )
	{
		return;
	}

	jumpReadyTime = gameLocal.time + pm_jumpdelay.GetInteger();

	const float keep = idMath::ClampFloat( 0.0f, 1.0f, pm_landspeedscale.GetFloat() );
	if( keep < 1.0f )
	{
		const idVec3 velocity = physics->GetLinearVelocity();
		const idVec3 vertical = ( velocity * down ) * down;
		physics->SetLinearVelocity( vertical + ( velocity - vertical ) * keep );
	}
}

/*
==============
UnholyPlayer::WeaponGait

C'est elle qui choisit l'animation de l'arme, et la dispersion du tir.
==============
*/
UnholyPlayer::weaponGait_t UnholyPlayer::WeaponGait() const
{
	const idPhysics_Player* physics = PlayerPhysics();
	const idVec3& down = physics->GetGravityNormal();
	const idVec3 velocity = physics->GetLinearVelocity();
	const float speed = ( velocity - ( velocity * down ) * down ).Length();
	const bool moving = speed > 10.0f;

	if( physics->IsCrouching() )
	{
		return moving ? GAIT_CROUCH_WALK : GAIT_CROUCH_IDLE;
	}
	if( !moving )
	{
		return GAIT_IDLE;
	}
	if( ( usercmd.buttons & BUTTON_RUN ) && speed > pm_walkspeed.GetFloat() + 5.0f )
	{
		return GAIT_RUN;
	}
	return GAIT_WALK;
}

/*
==============
UnholyPlayer::UpdateWeaponScript

Le script de l'arme lit deux variables que le moteur ne connait pas : on les
lui ecrit ici, avant que l'arme ne pense. Une arme dont le script ne les
declare pas les ignore.
==============
*/
void UnholyPlayer::UpdateWeaponScript()
{
	aiming = ( usercmd.buttons & BUTTON_ZOOM ) != 0 && WeaponGait() != GAIT_RUN;

	idWeapon* gun = weapon.GetEntity();
	if( gun == NULL || !gun->scriptObject.HasObject() )
	{
		return;
	}
	byte* aim = gun->scriptObject.GetVariable( "UNHOLY_AIM", ev_float );
	if( aim != NULL )
	{
		*reinterpret_cast<float*>( aim ) = aiming ? 1.0f : 0.0f;
	}
	byte* gait = gun->scriptObject.GetVariable( "UNHOLY_GAIT", ev_float );
	if( gait != NULL )
	{
		*reinterpret_cast<float*>( gait ) = static_cast<float>( WeaponGait() );
	}
}

/*
==============
UnholyPlayer::RunMoveTest

Le banc d'essai prend la place du clavier et de la souris : il donne les
commandes, et tient la vue lui-meme.
==============
*/
void UnholyPlayer::RunMoveTest()
{
	// Une demande faite pendant le chargement attend que la partie tourne :
	// l'horloge du jeu n'est pas encore celle de la partie.
	const char* request = unholy_moveTest.GetString();
	if( request[0] != '\0' && gameLocal.GameState() == GAMESTATE_ACTIVE )
	{
		const idStr name = request;
		unholy_moveTest.SetString( "" );
		if( !moveTest.Start( name.c_str(), gameLocal.time, PlayerPhysics()->PlayerGetOrigin(), viewAngles.yaw ) )
		{
			UnholyMoveTest::ListScenarios();
		}
		testYaw = viewAngles.yaw;
	}

	if( !moveTest.IsRunning() )
	{
		return;
	}
	if( health <= 0 || noclip || spectating )
	{
		moveTest.Stop();
		return;
	}

	unholyMoveDrive_t drive;
	moveTest.Drive( gameLocal.time, gameLocal.time - gameLocal.previousTime, drive );
	if( !moveTest.IsRunning() )
	{
		return;
	}

	if( drive.resetToStart )
	{
		// Chaque scenario repart frais : au meme endroit, arrete, endurance
		// pleine, rien en attente sur le saut.
		PlayerPhysics()->SetOrigin( moveTest.StartOrigin() );
		PlayerPhysics()->SetLinearVelocity( vec3_origin );
		testYaw = moveTest.StartYaw();
		stamina = pm_stamina.GetFloat();
		jumpReadyTime = 0;
		jumpLatched = false;
	}
	testYaw += drive.yawDelta;
	SetViewAngles( idAngles( drive.pitch, testYaw, 0.0f ) );

	usercmd.forwardmove = drive.forward;
	usercmd.rightmove = drive.right;
	usercmd.buttons = ( usercmd.buttons & ~( BUTTON_RUN | BUTTON_CROUCH | BUTTON_JUMP | BUTTON_ATTACK | BUTTON_ZOOM ) ) | drive.buttons;
	if( drive.impulse != 0 )
	{
		usercmd.impulse = drive.impulse;
		usercmd.impulseSequence++;
	}
}

/*
==============
UnholyPlayer::MeasureMoveTest
==============
*/
void UnholyPlayer::MeasureMoveTest()
{
	if( !moveTest.IsRunning() )
	{
		return;
	}

	const idPhysics_Player* physics = PlayerPhysics();
	unholyMoveSample_t sample;
	sample.time = gameLocal.time;
	sample.origin = physics->PlayerGetOrigin();
	sample.velocity = physics->GetLinearVelocity();
	sample.gravityNormal = physics->GetGravityNormal();
	sample.onGround = physics->HasGroundContacts();
	sample.jumped = physics->HasJumped();
	sample.crouching = physics->IsCrouching();
	sample.eyeHeight = EyeHeight();
	sample.stamina = stamina;
	const idWeapon* gun = weapon.GetEntity();
	sample.clip = gun != NULL ? gun->AmmoInClip() : -1;
	sample.reserve = gun != NULL ? gun->AmmoAvailable() : -1;
	moveTest.Measure( sample );
}

/*
==============
UnholyPlayer::Gait
==============
*/
const char* UnholyPlayer::Gait() const
{
	const idPhysics_Player* physics = PlayerPhysics();
	if( !physics->HasGroundContacts() )
	{
		return "en l'air";
	}
	if( physics->IsCrouching() )
	{
		return "accroupi";
	}

	const idVec3& down = physics->GetGravityNormal();
	const idVec3 velocity = physics->GetLinearVelocity();
	const float speed = ( velocity - ( velocity * down ) * down ).Length();
	if( speed < 1.0f )
	{
		return "immobile";
	}
	if( ( usercmd.buttons & BUTTON_RUN ) && speed > pm_walkspeed.GetFloat() + 1.0f )
	{
		return "course";
	}
	return "marche";
}

/*
==============
UnholyPlayer::LogMovement
==============
*/
void UnholyPlayer::LogMovement() const
{
	const idPhysics_Player* physics = PlayerPhysics();
	const idVec3& down = physics->GetGravityNormal();
	const idVec3 velocity = physics->GetLinearVelocity();
	const idVec3 origin = physics->PlayerGetOrigin();
	const float vertical = velocity * down;
	const float speed = ( velocity - vertical * down ).Length();

	gameLocal.Printf( "[deplacement] %d pos %.1f %.1f %.1f vitesse %.1f chute %.1f %s endurance %.2f yeux %.1f\n",
					  gameLocal.time, origin.x, origin.y, origin.z, speed, vertical, Gait(), stamina, EyeHeight() );
}

/*
==============
UnholyPlayer::DrawHUD
==============
*/
void UnholyPlayer::DrawHUD( idMenuHandler_HUD* hudManager )
{
	idPlayer::DrawHUD( hudManager );

	if( g_showHud.GetBool() && health > 0 && !spectating )
	{
		DrawWeaponHud();
	}
	if( unholy_showMove.GetBool() )
	{
		DrawMovementReadout();
	}
}

/*
==============
UnholyPlayer::DrawWeaponHud

Le reticule et les munitions, rien d'autre. Le reticule s'ouvre avec la
dispersion du tir, et disparait quand on epaule (la visee du fusil prend le
relais), qu'on court ou qu'on recharge.
==============
*/
void UnholyPlayer::DrawWeaponHud() const
{
	const idWeapon* gun = weapon.GetEntity();
	if( gun == NULL )
	{
		return;
	}

	const float width = renderSystem->GetVirtualWidth();
	const float height = renderSystem->GetVirtualHeight();
	const idMaterial* white = declManager->FindMaterial( "_white" );
	const weaponGait_t gait = WeaponGait();

	if( !aiming && gait != GAIT_RUN && !gun->IsReloading() )
	{
		// L'ecart des branches : l'angle de dispersion rapporte au champ de vision.
		float spread = gun->spawnArgs.GetFloat( "spread_hip" );
		if( gait == GAIT_WALK || gait == GAIT_CROUCH_WALK )
		{
			spread += gun->spawnArgs.GetFloat( "spread_move" );
		}
		const float halfFov = DEG2RAD( g_fov.GetFloat() * 0.5f );
		const float gap = Max( 2.0f, idMath::Tan( DEG2RAD( spread ) ) / idMath::Tan( halfFov ) * width * 0.5f );
		const float length = 5.0f;
		const float thick = 1.0f;
		const float cx = width * 0.5f;
		const float cy = height * 0.5f;

		renderSystem->SetColor4( 0.92f, 0.9f, 0.84f, 0.8f );
		renderSystem->DrawStretchPic( cx - gap - length, cy - thick * 0.5f, length, thick, 0, 0, 1, 1, white );
		renderSystem->DrawStretchPic( cx + gap, cy - thick * 0.5f, length, thick, 0, 0, 1, 1, white );
		renderSystem->DrawStretchPic( cx - thick * 0.5f, cy - gap - length, thick, length, 0, 0, 1, 1, white );
		renderSystem->DrawStretchPic( cx - thick * 0.5f, cy + gap, thick, length, 0, 0, 1, 1, white );
	}

	// Les munitions, en bas a droite : le chargeur, puis la reserve.
	const int clip = gun->AmmoInClip();
	const int reserve = gun->AmmoAvailable();
	const idVec4 color = clip > gun->spawnArgs.GetInt( "lowAmmo", "8" ) ? idVec4( 0.92f, 0.9f, 0.84f, 0.85f ) : idVec4( 1.0f, 0.55f, 0.35f, 0.9f );
	const idStr clipText = va( "%d", clip );
	const idStr reserveText = va( "/ %d", reserve );
	const int right = static_cast<int>( width ) - 24;
	const int bottom = static_cast<int>( height ) - 30;
	const int reserveX = right - reserveText.Length() * SMALLCHAR_WIDTH;
	renderSystem->DrawSmallStringExt( reserveX, bottom + BIGCHAR_HEIGHT - SMALLCHAR_HEIGHT, reserveText.c_str(), idVec4( 0.8f, 0.78f, 0.72f, 0.7f ), true );
	renderSystem->DrawBigStringExt( reserveX - 6 - clipText.Length() * BIGCHAR_WIDTH, bottom, clipText.c_str(), color, true );
	renderSystem->SetColor4( 1.0f, 1.0f, 1.0f, 1.0f );
}

/*
==============
UnholyPlayer::DrawMovementReadout

Le releve du deplacement, en haut a gauche. Les chiffres en metres sont ceux
qu'on compare au reel ; ceux en unites, ceux qu'on tape a la console.
==============
*/
void UnholyPlayer::DrawMovementReadout() const
{
	const idPhysics_Player* physics = PlayerPhysics();
	const idVec3& down = physics->GetGravityNormal();
	const idVec3 velocity = physics->GetLinearVelocity();
	const float speed = ( velocity - ( velocity * down ) * down ).Length();
	const int jumpWait = pm_jumpdelay.GetInteger() > 0 ? jumpReadyTime - gameLocal.time : 0;

	const idVec4 color( 0.85f, 0.85f, 0.8f, 1.0f );
	const int x = 16;
	const int step = SMALLCHAR_HEIGHT + 2;
	int y = 48;

	renderSystem->DrawSmallStringExt( x, y, va( "vitesse    %5.2f m/s  %4.0f u/s", speed * METERS_PER_UNIT, speed ), color, true );
	y += step;
	renderSystem->DrawSmallStringExt( x, y, va( "allure     %s", Gait() ), color, true );
	y += step;
	renderSystem->DrawSmallStringExt( x, y, va( "endurance  %4.1f / %.1f s", stamina, pm_stamina.GetFloat() ), color, true );
	y += step;
	renderSystem->DrawSmallStringExt( x, y, jumpWait > 0 ? va( "saut       dans %d ms", jumpWait ) : "saut       libre", color, true );
	y += step;
	renderSystem->DrawSmallStringExt( x, y, va( "yeux       %4.1f u  %4.2f m", EyeHeight(), EyeHeight() * METERS_PER_UNIT ), color, true );
}
