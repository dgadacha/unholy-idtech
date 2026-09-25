/*
===========================================================================

UNHOLY -- code de jeu. GPL-3.0, comme le moteur RBDOOM-3-BFG auquel il est lie.

===========================================================================
*/

#ifndef __UNHOLY_TARGET_H__
#define __UNHOLY_TARGET_H__

/*
	La cible d'entrainement.

	C'est l'ennemi simple que demande le brief pour la migration room : elle
	recoit des degats et meurt. Une silhouette de contreplaque faite de
	brushes, dont l'origine est posee a sa base : touchee, elle sonne ; sa
	sante a zero, elle bascule en arriere, loin du tireur, reste a terre
	quelques secondes, puis se releve. On peut ainsi tirer encore sans
	recharger la carte.

	Le moteur fait le reste : la collision, les degats (idEntity::Damage), le
	trou de la balle et le son de l'impact, selon la matiere du bois.
*/
class UnholyTarget : public idEntity
{
public:
	CLASS_PROTOTYPE( UnholyTarget );

							UnholyTarget();

	void					Spawn();
	void					Save( idSaveGame* savefile ) const;
	void					Restore( idRestoreGame* savefile );

	virtual void			Think();
	virtual bool			Pain( idEntity* inflictor, idEntity* attacker, int damage, const idVec3& dir, int location );
	virtual void			Killed( idEntity* inflictor, idEntity* attacker, int damage, const idVec3& dir, int location );

private:
	enum targetState_t
	{
		TARGET_STANDING,
		TARGET_FALLING,
		TARGET_DOWN,
		TARGET_RISING
	};

	void					SetTilt( float fraction );

	targetState_t			state;
	int						stateTime;		// debut de l'etat en cours, ms
	int						fallTime;		// ms
	int						downTime;
	int						riseTime;
	int						maxHealth;
	float					fallSign;		// de quel cote elle tombe
	idMat3					standingAxis;
};

#endif /* !__UNHOLY_TARGET_H__ */
