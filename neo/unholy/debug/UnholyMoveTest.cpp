/*
===========================================================================

UNHOLY -- code de jeu. GPL-3.0, comme le moteur RBDOOM-3-BFG auquel il est lie.

===========================================================================
*/

#include "precompiled.h"
#pragma hdrstop

#include "d3xp/Game_local.h"
#include "debug/UnholyMoveTest.h"

// Un pouce en metres : les unites du moteur sont des pouces.
static const float METERS_PER_UNIT = 0.0254f;

// Pause au depart de chaque scenario, le temps que le joueur replace s'arrete.
static const int REST_MSEC = 500;

enum unholyMoveReport_t
{
	REPORT_NONE,
	REPORT_ACCEL,		// temps pour prendre l'allure attendue
	REPORT_STOP,		// temps et distance d'arret
	REPORT_STAND,		// temps pour se relever
	REPORT_JUMP,		// hauteur et duree d'un saut
	REPORT_JUMPS,		// nombre de sauts et intervalle le plus court
	REPORT_SPEED,		// vitesse moyenne et maximale
	REPORT_STAMINA,		// duree de la course pleine, recuperation
	REPORT_AMMO			// chargeur et reserve, avant et apres
};

// Saut : 0 jamais, JUMP_ONCE un appui a la premiere image, JUMP_HOLD tenu,
// n > 1 un appui d'une image toutes les n images.
static const int JUMP_ONCE = -1;
static const int JUMP_HOLD = 1;

struct unholyMoveStep_t
{
	const char*			label;
	int					duration;		// ms
	int					forward;
	int					right;
	int					buttons;
	int					jump;
	float				yawSpeed;		// degres par seconde, positif vers la gauche
	unholyMoveReport_t	report;
	int					impulse;		// commande donnee a la premiere image, 0 sinon
	float				pitch;			// inclinaison de la vue, en degres vers le bas
};

// La commande de rechargement (framework/UsercmdGen.h).
static const int IMPULSE_RELOAD = IMPULSE_13;

struct unholyMoveScenario_t
{
	const char*				name;
	const char*				description;
	const unholyMoveStep_t*	steps;
	int						numSteps;
};

static const unholyMoveStep_t walkSteps[] =
{
	{ "depart",		3000,	127,	0,		0,				0,	0.0f,	REPORT_ACCEL },
	{ "arret",		1500,	0,		0,		0,				0,	0.0f,	REPORT_STOP },
};

static const unholyMoveStep_t sprintSteps[] =
{
	{ "depart",		3000,	127,	0,		BUTTON_RUN,		0,	0.0f,	REPORT_ACCEL },
	{ "arret",		1500,	0,		0,		0,				0,	0.0f,	REPORT_STOP },
};

static const unholyMoveStep_t crouchSteps[] =
{
	{ "accroupi",	2500,	127,	0,		BUTTON_CROUCH,	0,	0.0f,	REPORT_ACCEL },
	{ "arret",		1000,	0,		0,		BUTTON_CROUCH,	0,	0.0f,	REPORT_STOP },
	{ "debout",		1000,	0,		0,		0,				0,	0.0f,	REPORT_STAND },
};

static const unholyMoveStep_t jumpSteps[] =
{
	{ "saut",			1600,	0,		0,		0,		JUMP_ONCE,	0.0f,	REPORT_JUMP },
	{ "saut tenu",		3000,	0,		0,		0,		JUMP_HOLD,	0.0f,	REPORT_JUMPS },
	{ "sauts repetes",	4000,	0,		0,		0,		2,			0.0f,	REPORT_JUMPS },
};

// Sauter en boucle en courant : le bunny hop. Il ne doit rien rapporter.
static const unholyMoveStep_t bhopSteps[] =
{
	{ "elan",		1500,	127,	0,		BUTTON_RUN,		0,	0.0f,	REPORT_SPEED },
	{ "bhop",		5000,	127,	0,		BUTTON_RUN,		2,	0.0f,	REPORT_SPEED },
};

// Sauter en boucle en tournant, avant et cote tenus : le strafe jump.
static const unholyMoveStep_t strafeSteps[] =
{
	{ "elan",		1500,	127,	0,		BUTTON_RUN,		0,	0.0f,		REPORT_SPEED },
	{ "strafe",		5000,	127,	127,	BUTTON_RUN,		2,	-120.0f,	REPORT_SPEED },
};

// Courir jusqu'a epuisement, en tournant large pour rester dans l'aire d'essai.
static const unholyMoveStep_t staminaSteps[] =
{
	{ "course",		12000,	127,	0,		BUTTON_RUN,		0,	25.0f,	REPORT_STAMINA },
	{ "repos",		12000,	0,		0,		0,				0,	0.0f,	REPORT_STAMINA },
};

// Tenir la detente, puis recharger : ce que le chargeur et la reserve deviennent.
// La vue garde la direction du depart, baissee de quoi viser le torse d'une
// cible a quatre metres.
static const float FIRE_PITCH = 7.5f;
static const unholyMoveStep_t fireSteps[] =
{
	{ "arme prete",	1500,	0,		0,		0,								0,	0.0f,	REPORT_AMMO,	0,				FIRE_PITCH },
	{ "rafale",		1500,	0,		0,		BUTTON_ATTACK,					0,	0.0f,	REPORT_AMMO,	0,				FIRE_PITCH },
	{ "epaule",		1200,	0,		0,		BUTTON_ZOOM | BUTTON_ATTACK,	0,	0.0f,	REPORT_AMMO,	0,				FIRE_PITCH },
	{ "recharge",	5000,	0,		0,		0,								0,	0.0f,	REPORT_AMMO,	IMPULSE_RELOAD,	FIRE_PITCH },
};

#define SCENARIO( name, description, steps ) { name, description, steps, sizeof( steps ) / sizeof( steps[0] ) }

static const unholyMoveScenario_t scenarios[] =
{
	SCENARIO( "marche",		"prendre l'allure, puis s'arreter",					walkSteps ),
	SCENARIO( "course",		"prendre la course, puis s'arreter",				sprintSteps ),
	SCENARIO( "accroupi",	"avancer accroupi, s'arreter, se relever",			crouchSteps ),
	SCENARIO( "saut",		"un saut, le bouton tenu, puis des appuis repetes",	jumpSteps ),
	SCENARIO( "bhop",		"sauter en boucle en courant",						bhopSteps ),
	SCENARIO( "strafe",		"sauter en boucle en tournant, avant et cote",		strafeSteps ),
	SCENARIO( "endurance",	"courir jusqu'a epuisement, puis recuperer",		staminaSteps ),
	SCENARIO( "tir",		"une rafale, une rafale epaulee, un rechargement",	fireSteps ),
};
static const int numScenarios = sizeof( scenarios ) / sizeof( scenarios[0] );

// "tout" enchaine tout sauf l'endurance, qui dure pres d'une demi-minute.
static const unholyMoveScenario_t* allScenarios[] =
{
	&scenarios[0], &scenarios[1], &scenarios[2], &scenarios[3], &scenarios[4], &scenarios[5]
};

static float HorizontalSpeed( const unholyMoveSample_t& sample )
{
	const idVec3 vertical = ( sample.velocity * sample.gravityNormal ) * sample.gravityNormal;
	return ( sample.velocity - vertical ).Length();
}

// Une duree lisible, ou "--" quand la mesure n'a pas eu lieu.
static idStr Seconds( int msec )
{
	if( msec < 0 )
	{
		return "--";
	}
	return va( "%.2f s", msec * 0.001f );
}

/*
================
UnholyMoveTest::UnholyMoveTest
================
*/
UnholyMoveTest::UnholyMoveTest()
{
	queue = NULL;
	queueLength = 0;
	queueIndex = 0;
	scenario = NULL;
	stepIndex = -1;
	stepStart = 0;
	stepFrame = 0;
	pendingReset = false;
	restUntil = 0;
	startOrigin.Zero();
	startYaw = 0.0f;
	hasSample = false;
	memset( &last, 0, sizeof( last ) );
}

/*
================
UnholyMoveTest::ListScenarios
================
*/
void UnholyMoveTest::ListScenarios()
{
	gameLocal.Printf( "unholy_moveTest <scenario> :\n" );
	for( int i = 0; i < numScenarios; i++ )
	{
		gameLocal.Printf( "  %-10s %s\n", scenarios[i].name, scenarios[i].description );
	}
	gameLocal.Printf( "  %-10s les six premiers, a la suite\n", "tout" );
	gameLocal.Printf( "  (tir : la vue garde la direction du depart ; viser d'abord une cible)\n" );
}

/*
================
UnholyMoveTest::Start
================
*/
bool UnholyMoveTest::Start( const char* name, int time, const idVec3& origin, float yaw )
{
	static const unholyMoveScenario_t* single[1];

	if( !idStr::Icmp( name, "tout" ) )
	{
		queue = allScenarios;
		queueLength = sizeof( allScenarios ) / sizeof( allScenarios[0] );
	}
	else
	{
		const unholyMoveScenario_t* found = NULL;
		for( int i = 0; i < numScenarios; i++ )
		{
			if( !idStr::Icmp( name, scenarios[i].name ) )
			{
				found = &scenarios[i];
			}
		}
		if( found == NULL )
		{
			return false;
		}
		single[0] = found;
		queue = single;
		queueLength = 1;
	}

	startOrigin = origin;
	startYaw = yaw;
	queueIndex = 0;
	BeginScenario( time );

	gameLocal.Printf( "[mouvement] depart en ( %.0f %.0f %.0f ), lacet %.0f\n", origin.x, origin.y, origin.z, yaw );
	gameLocal.Printf( "[mouvement] reglages : marche %.0f, course %.0f, accroupi %.0f u/s ; acceleration %.1f, frottement %.1f, arret %.0f, air %.2f, mode %d ; saut %.0f u, delai %d ms, reception %.2f\n",
					  pm_walkspeed.GetFloat(), pm_runspeed.GetFloat(), pm_crouchspeed.GetFloat(),
					  pm_accelerate.GetFloat(), pm_friction.GetFloat(), pm_stopspeed.GetFloat(), pm_airaccelerate.GetFloat(), pm_accelmode.GetInteger(),
					  pm_jumpheight.GetFloat(), cvarSystem->GetCVarInteger( "pm_jumpdelay" ), cvarSystem->GetCVarFloat( "pm_landspeedscale" ) );
	return true;
}

/*
================
UnholyMoveTest::Stop
================
*/
void UnholyMoveTest::Stop()
{
	if( scenario != NULL )
	{
		gameLocal.Printf( "[mouvement] fin\n" );
	}
	scenario = NULL;
	queue = NULL;
	stepIndex = -1;
}

/*
================
UnholyMoveTest::BeginScenario
================
*/
void UnholyMoveTest::BeginScenario( int time )
{
	scenario = queue[queueIndex];
	stepIndex = -1;
	pendingReset = true;
	restUntil = time + REST_MSEC;
	hasSample = false;
	gameLocal.Printf( "[mouvement] -- %s : %s\n", scenario->name, scenario->description );
}

/*
================
UnholyMoveTest::BeginStep

La premiere image de l'etape simule deja l'intervalle qui la precede : le
chronometre part donc une image plus tot.
================
*/
void UnholyMoveTest::BeginStep( int time )
{
	stepStart = time - ( gameLocal.time - gameLocal.previousTime );
	stepFrame = 0;
	stepStartZ = hasSample ? last.origin.z : 0.0f;
	maxSpeed = 0.0f;
	sumSpeed = 0.0f;
	numSpeed = 0;
	distance = 0.0f;
	reach[0] = reach[1] = reach[2] = -1;
	stopTime = -1;
	stopDistance = 0.0f;
	takeoffs = 0;
	lastTakeoff = -1;
	minTakeoffInterval = -1;
	firstTakeoff = -1;
	firstLanding = -1;
	apex = 0.0f;
	eyeReached = -1;
	fullSprintEnd = -1;
	walkReached = -1;
	staminaFull = -1;
	clipStart = hasSample ? last.clip : -1;
	reserveStart = hasSample ? last.reserve : -1;
}

/*
================
UnholyMoveTest::ExpectedSpeed
================
*/
float UnholyMoveTest::ExpectedSpeed() const
{
	const unholyMoveStep_t& step = scenario->steps[stepIndex];
	if( step.buttons & BUTTON_CROUCH )
	{
		return pm_crouchspeed.GetFloat();
	}
	if( step.buttons & BUTTON_RUN )
	{
		return pm_runspeed.GetFloat();
	}
	return pm_walkspeed.GetFloat();
}

/*
================
UnholyMoveTest::Drive
================
*/
void UnholyMoveTest::Drive( int time, int frameMsec, unholyMoveDrive_t& drive )
{
	drive.forward = 0;
	drive.right = 0;
	drive.buttons = 0;
	drive.impulse = 0;
	drive.yawDelta = 0.0f;
	drive.pitch = 0.0f;
	drive.resetToStart = false;

	if( scenario == NULL )
	{
		return;
	}

	if( pendingReset )
	{
		drive.resetToStart = true;
		pendingReset = false;
	}

	if( stepIndex < 0 )
	{
		if( time < restUntil )
		{
			return;
		}
		stepIndex = 0;
		BeginStep( time );
	}
	else if( time - stepStart > scenario->steps[stepIndex].duration )
	{
		EndStep();
		stepIndex++;
		if( stepIndex >= scenario->numSteps )
		{
			queueIndex++;
			if( queueIndex >= queueLength )
			{
				Stop();
				return;
			}
			BeginScenario( time );
			drive.resetToStart = true;
			pendingReset = false;
			return;
		}
		BeginStep( time );
	}

	const unholyMoveStep_t& step = scenario->steps[stepIndex];
	drive.forward = step.forward;
	drive.right = step.right;
	drive.buttons = step.buttons;

	bool jump = false;
	if( step.jump == JUMP_HOLD )
	{
		jump = true;
	}
	else if( step.jump == JUMP_ONCE )
	{
		jump = ( stepFrame == 0 );
	}
	else if( step.jump > 1 )
	{
		jump = ( stepFrame % step.jump ) == 0;
	}
	if( jump )
	{
		drive.buttons |= BUTTON_JUMP;
	}
	if( stepFrame == 0 )
	{
		drive.impulse = step.impulse;
	}
	drive.pitch = step.pitch;

	drive.yawDelta = step.yawSpeed * frameMsec * 0.001f;
	stepFrame++;
}

/*
================
UnholyMoveTest::Measure
================
*/
void UnholyMoveTest::Measure( const unholyMoveSample_t& sample )
{
	if( scenario == NULL )
	{
		return;
	}

	if( stepIndex < 0 || !hasSample )
	{
		last = sample;
		hasSample = true;
		return;
	}

	const unholyMoveStep_t& step = scenario->steps[stepIndex];
	const int elapsed = sample.time - stepStart;
	const float speed = HorizontalSpeed( sample );

	idVec3 moved = sample.origin - last.origin;
	moved -= ( moved * sample.gravityNormal ) * sample.gravityNormal;
	distance += moved.Length();

	maxSpeed = Max( maxSpeed, speed );
	sumSpeed += speed;
	numSpeed++;

	const float expected = ExpectedSpeed();
	static const float fractions[3] = { 0.5f, 0.9f, 0.99f };
	for( int i = 0; i < 3; i++ )
	{
		if( reach[i] < 0 && speed >= expected * fractions[i] )
		{
			reach[i] = elapsed;
		}
	}

	if( stopTime < 0 && speed < 1.0f )
	{
		stopTime = elapsed;
		stopDistance = distance;
	}

	if( sample.jumped )
	{
		if( lastTakeoff >= 0 )
		{
			const int interval = sample.time - lastTakeoff;
			if( minTakeoffInterval < 0 || interval < minTakeoffInterval )
			{
				minTakeoffInterval = interval;
			}
		}
		if( firstTakeoff < 0 )
		{
			firstTakeoff = sample.time;
		}
		lastTakeoff = sample.time;
		takeoffs++;
	}
	if( firstTakeoff >= 0 && firstLanding < 0 && !last.onGround && sample.onGround )
	{
		firstLanding = sample.time;
	}
	apex = Max( apex, sample.origin.z - stepStartZ );

	if( eyeReached < 0 )
	{
		const float target = ( step.buttons & BUTTON_CROUCH ) ? pm_crouchviewheight.GetFloat() : pm_normalviewheight.GetFloat();
		if( idMath::Fabs( sample.eyeHeight - target ) < 1.0f )
		{
			eyeReached = elapsed;
		}
	}

	if( step.report == REPORT_STAMINA )
	{
		if( step.buttons & BUTTON_RUN )
		{
			// La course pleine ne se compte qu'une fois l'allure prise.
			if( fullSprintEnd < 0 && reach[2] >= 0 && speed < 0.98f * pm_runspeed.GetFloat() )
			{
				fullSprintEnd = elapsed;
			}
			if( fullSprintEnd >= 0 && walkReached < 0 && speed <= 1.02f * pm_walkspeed.GetFloat() )
			{
				walkReached = elapsed;
			}
		}
		else if( staminaFull < 0 && sample.stamina >= pm_stamina.GetFloat() - 0.01f )
		{
			staminaFull = elapsed;
		}
	}

	last = sample;
}

/*
================
UnholyMoveTest::EndStep
================
*/
void UnholyMoveTest::EndStep()
{
	const unholyMoveStep_t& step = scenario->steps[stepIndex];
	const float expected = ExpectedSpeed();
	// Copie : le tampon de va() tourne, et l'impression s'en sert aussi.
	const idStr prefixText = va( "[mouvement] %s / %s :", scenario->name, step.label );
	const char* prefix = prefixText.c_str();

	switch( step.report )
	{
		case REPORT_ACCEL:
			gameLocal.Printf( "%s allure %.0f u/s (%.2f m/s) attendue, %.0f atteinte ; 50 %% en %s, 90 %% en %s, 99 %% en %s ; yeux a %.0f u en %s\n",
							  prefix, expected, expected * METERS_PER_UNIT, maxSpeed,
							  Seconds( reach[0] ).c_str(), Seconds( reach[1] ).c_str(), Seconds( reach[2] ).c_str(),
							  last.eyeHeight, Seconds( eyeReached ).c_str() );
			break;

		case REPORT_STOP:
			gameLocal.Printf( "%s arret en %s sur %.0f u (%.0f cm)\n",
							  prefix, Seconds( stopTime ).c_str(), stopDistance, stopDistance * METERS_PER_UNIT * 100.0f );
			break;

		case REPORT_STAND:
			gameLocal.Printf( "%s yeux a %.0f u en %s\n", prefix, last.eyeHeight, Seconds( eyeReached ).c_str() );
			break;

		case REPORT_JUMP:
			gameLocal.Printf( "%s hauteur %.1f u (%.0f cm), %s en l'air\n",
							  prefix, apex, apex * METERS_PER_UNIT * 100.0f,
							  Seconds( ( firstTakeoff >= 0 && firstLanding >= 0 ) ? firstLanding - firstTakeoff : -1 ).c_str() );
			break;

		case REPORT_JUMPS:
			gameLocal.Printf( "%s %d saut(s), %s au plus court entre deux decollages\n",
							  prefix, takeoffs, Seconds( minTakeoffInterval ).c_str() );
			break;

		case REPORT_SPEED:
			gameLocal.Printf( "%s vitesse moyenne %.0f u/s, maximale %.0f u/s (course : %.0f) ; %d saut(s), %.0f u parcourus\n",
							  prefix, numSpeed ? sumSpeed / numSpeed : 0.0f, maxSpeed, pm_runspeed.GetFloat(), takeoffs, distance );
			break;

		case REPORT_STAMINA:
			if( step.buttons & BUTTON_RUN )
			{
				gameLocal.Printf( "%s course pleine %s, retour au pas a %s, endurance restante %.1f s\n",
								  prefix, Seconds( fullSprintEnd ).c_str(), Seconds( walkReached ).c_str(), last.stamina );
			}
			else
			{
				gameLocal.Printf( "%s endurance pleine (%.1f s) apres %s\n",
								  prefix, pm_stamina.GetFloat(), Seconds( staminaFull ).c_str() );
			}
			break;

		case REPORT_AMMO:
			gameLocal.Printf( "%s chargeur %d -> %d, reserve %d -> %d\n",
							  prefix, clipStart, last.clip, reserveStart, last.reserve );
			break;

		default:
			break;
	}
}
