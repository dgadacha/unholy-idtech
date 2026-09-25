/*
===========================================================================

UNHOLY -- code de jeu. GPL-3.0, comme le moteur RBDOOM-3-BFG auquel il est lie.

===========================================================================
*/

#include "precompiled.h"
#pragma hdrstop

#include "d3xp/Game_local.h"
#include "world/UnholyTarget.h"

// La planche couchee n'est pas tout a fait a plat : elle retombe sur son bord.
static const float FALLEN_ANGLE = 84.0f;

CLASS_DECLARATION( idEntity, UnholyTarget )
END_CLASS

/*
================
UnholyTarget::UnholyTarget
================
*/
UnholyTarget::UnholyTarget()
{
	state = TARGET_STANDING;
	stateTime = 0;
	fallTime = 350;
	downTime = 4000;
	riseTime = 600;
	maxHealth = 75;
	fallSign = 1.0f;
	standingAxis.Identity();
}

/*
================
UnholyTarget::Spawn
================
*/
void UnholyTarget::Spawn()
{
	maxHealth = spawnArgs.GetInt( "health", "75" );
	health = maxHealth;
	fl.takedamage = true;
	fallTime = SEC2MS( spawnArgs.GetFloat( "fall_time", "0.35" ) );
	downTime = SEC2MS( spawnArgs.GetFloat( "down_time", "4" ) );
	riseTime = SEC2MS( spawnArgs.GetFloat( "rise_time", "0.6" ) );
	standingAxis = GetPhysics()->GetAxis();
	state = TARGET_STANDING;
}

/*
================
UnholyTarget::Save
================
*/
void UnholyTarget::Save( idSaveGame* savefile ) const
{
	savefile->WriteInt( state );
	savefile->WriteInt( stateTime );
	savefile->WriteInt( fallTime );
	savefile->WriteInt( downTime );
	savefile->WriteInt( riseTime );
	savefile->WriteInt( maxHealth );
	savefile->WriteFloat( fallSign );
	savefile->WriteMat3( standingAxis );
}

/*
================
UnholyTarget::Restore
================
*/
void UnholyTarget::Restore( idRestoreGame* savefile )
{
	int value;
	savefile->ReadInt( value );
	state = static_cast<targetState_t>( value );
	savefile->ReadInt( stateTime );
	savefile->ReadInt( fallTime );
	savefile->ReadInt( downTime );
	savefile->ReadInt( riseTime );
	savefile->ReadInt( maxHealth );
	savefile->ReadFloat( fallSign );
	savefile->ReadMat3( standingAxis );
}

/*
================
UnholyTarget::Pain
================
*/
bool UnholyTarget::Pain( idEntity* inflictor, idEntity* attacker, int damage, const idVec3& dir, int location )
{
	StartSound( "snd_hit", SND_CHANNEL_BODY, 0, false, NULL );
	return true;
}

/*
================
UnholyTarget::Killed

La planche bascule en arriere, vue du tireur : du cote ou partait la balle.
================
*/
void UnholyTarget::Killed( idEntity* inflictor, idEntity* attacker, int damage, const idVec3& dir, int location )
{
	if( state != TARGET_STANDING )
	{
		return;
	}
	fl.takedamage = false;
	fallSign = ( dir * standingAxis[0] ) >= 0.0f ? 1.0f : -1.0f;
	state = TARGET_FALLING;
	stateTime = gameLocal.time;
	StartSound( "snd_hit", SND_CHANNEL_BODY, 0, false, NULL );
	BecomeActive( TH_THINK );
}

/*
================
UnholyTarget::SetTilt

Incline la planche autour de sa base, de debout (0) a couchee (1).
================
*/
void UnholyTarget::SetTilt( float fraction )
{
	const float angle = fallSign * FALLEN_ANGLE * idMath::ClampFloat( 0.0f, 1.0f, fraction );
	// La charniere est l'axe horizontal de la planche : son axe y local.
	const idRotation hinge( vec3_origin, standingAxis[1], angle );
	SetAxis( standingAxis * hinge.ToMat3() );
}

/*
================
UnholyTarget::Think
================
*/
void UnholyTarget::Think()
{
	const int elapsed = gameLocal.time - stateTime;

	switch( state )
	{
		case TARGET_FALLING:
		{
			// Elle tombe comme un poids : lentement d'abord, puis d'un coup.
			const float t = static_cast<float>( elapsed ) / fallTime;
			SetTilt( t * t );
			if( elapsed >= fallTime )
			{
				SetTilt( 1.0f );
				StartSound( "snd_fall", SND_CHANNEL_BODY2, 0, false, NULL );
				state = TARGET_DOWN;
				stateTime = gameLocal.time;
			}
			break;
		}
		case TARGET_DOWN:
			if( elapsed >= downTime )
			{
				state = TARGET_RISING;
				stateTime = gameLocal.time;
			}
			break;
		case TARGET_RISING:
		{
			// Elle se releve en ralentissant.
			const float t = idMath::ClampFloat( 0.0f, 1.0f, static_cast<float>( elapsed ) / riseTime );
			SetTilt( ( 1.0f - t ) * ( 1.0f - t ) );
			if( elapsed >= riseTime )
			{
				SetTilt( 0.0f );
				health = maxHealth;
				fl.takedamage = true;
				state = TARGET_STANDING;
				BecomeInactive( TH_THINK );
			}
			break;
		}
		default:
			BecomeInactive( TH_THINK );
			break;
	}

	Present();
}
