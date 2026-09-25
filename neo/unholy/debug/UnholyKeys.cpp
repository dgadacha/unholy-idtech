/*
===========================================================================

UNHOLY -- code de jeu. GPL-3.0, comme le moteur RBDOOM-3-BFG auquel il est lie.

===========================================================================
*/

#include "precompiled.h"
#pragma hdrstop

#include "d3xp/Game_local.h"

/*
	Presser une touche depuis la console.

	Un essai automatique ne peut pas taper dans la fenetre du jeu. Cette
	commande fait pour une touche ce que fait la boucle d'evenements du moteur
	(framework/EventLoop.cpp) : elle tient l'etat des touches a jour, puis
	passe l'evenement au moteur, qui le traite comme s'il venait du clavier.
	Elle presse, puis relache.

	Console : unholy_pressKey <touche>, avec les noms de `bind` (ESCAPE, TAB,
	MOUSE1, a...). Comme toute commande de mise au point, elle disparait des
	versions de vente.
*/
CONSOLE_COMMAND( unholy_pressKey, "presse puis relache une touche, comme le clavier : unholy_pressKey <touche>", NULL )
{
	if( args.Argc() != 2 )
	{
		common->Printf( "usage : unholy_pressKey <touche>, avec les noms de bind (ESCAPE, TAB, MOUSE1, a...)\n" );
		return;
	}

	const keyNum_t key = idKeyInput::StringToKeyNum( args.Argv( 1 ) );
	if( key == K_NONE )
	{
		common->Printf( "unholy_pressKey : touche inconnue, %s\n", args.Argv( 1 ) );
		return;
	}

	for( int down = 1; down >= 0; down-- )
	{
		sysEvent_t event;
		memset( &event, 0, sizeof( event ) );
		event.evType = SE_KEY;
		event.evValue = key;
		event.evValue2 = down;
		idKeyInput::PreliminaryKeyEvent( key, down != 0 );
		common->ProcessEvent( &event );
	}
	common->Printf( "unholy_pressKey : %s\n", idKeyInput::KeyNumToString( key ) );
}
