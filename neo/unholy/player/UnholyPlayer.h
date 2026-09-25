/*
===========================================================================

UNHOLY -- code de jeu. GPL-3.0, comme le moteur RBDOOM-3-BFG auquel il est lie.

===========================================================================
*/

#ifndef __UNHOLY_PLAYER_H__
#define __UNHOLY_PLAYER_H__

#include "debug/UnholyMoveTest.h"

/*
	Le joueur d'UNHOLY.

	Il reste un idPlayer : le moteur sait deja le faire marcher, regarder,
	courir, s'accroupir, sauter, monter les marches et buter contre les murs.
	On ne refait rien de tout cela.

	Ce qui est a UNHOLY, c'est le poids. Le militaire est lourd, precis, et
	bien plus lent qu'un joueur d'arene. Le moteur regle son deplacement par
	des variables pm_ ; la declaration du personnage les fixe toutes a son
	apparition, si bien qu'un camp et l'autre se reglent chacun dans leur
	fichier, et qu'on essaie une valeur a la console avant de l'y reporter.

	Trois regles s'ajoutent a ce que le moteur sait faire, parce qu'elles
	n'existent pas dans Doom 3 :

	- on ne court que vers l'avant (pm_sprintforwardonly) ;
	- on ne ressaute qu'apres un temps au sol, bouton relache (pm_jumpdelay) :
	  c'est ce qui tue le bunny hop ;
	- une reception coute de la vitesse (pm_landspeedscale).

	Le strafe jump, lui, tombe avec le calcul d'acceleration du moteur que
	choisit pm_accelmode 1.

	Le fusil est l'arme du moteur (idWeapon), menee par son script. Le joueur
	lui dit a chaque image s'il epaule et a quelle allure il va : le script
	choisit l'animation. On ne court pas en tirant ni en epaulant. Et le
	joueur dessine son interface : le reticule, qui s'ouvre avec la
	dispersion, et les munitions.
*/
class UnholyPlayer : public idPlayer
{
public:
	CLASS_PROTOTYPE( UnholyPlayer );

							UnholyPlayer();

	void					Spawn();
	void					Save( idSaveGame* savefile ) const;
	void					Restore( idRestoreGame* savefile );

	virtual void			Think();
	virtual void			DrawHUD( idMenuHandler_HUD* hudManager );

private:
	idPhysics_Player*		PlayerPhysics() const;

	void					ApplyMovementTuning();
	void					ApplyMovementRules( bool onGround );
	void					Landed( const idVec3& velocityBeforeLanding );

	// L'allure telle que le script de l'arme l'attend : les GAIT_ de
	// script/weapon_unholy_rifle.script, dans le meme ordre.
	enum weaponGait_t
	{
		GAIT_IDLE,
		GAIT_WALK,
		GAIT_RUN,
		GAIT_CROUCH_IDLE,
		GAIT_CROUCH_WALK
	};

	void					UpdateWeaponScript();
	weaponGait_t			WeaponGait() const;
	void					DrawWeaponHud() const;

	void					RunMoveTest();
	void					MeasureMoveTest();
	void					LogMovement() const;
	void					DrawMovementReadout() const;
	const char*				Gait() const;

	// saut : permis a partir de cet instant, et seulement bouton relache
	int						jumpReadyTime;
	bool					jumpLatched;
	// course : l'allure du decollage tient jusqu'a la reception
	bool					runAtTakeoff;
	// epaule, tel que le script de l'arme le voit
	bool					aiming;

	UnholyMoveTest			moveTest;
	float					testYaw;			// la vue, tenue par le banc d'essai
};

#endif /* !__UNHOLY_PLAYER_H__ */
