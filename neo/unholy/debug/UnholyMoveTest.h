/*
===========================================================================

UNHOLY -- code de jeu. GPL-3.0, comme le moteur RBDOOM-3-BFG auquel il est lie.

===========================================================================
*/

#ifndef __UNHOLY_MOVETEST_H__
#define __UNHOLY_MOVETEST_H__

/*
	Banc d'essai du deplacement.

	Un deplacement se juge en jouant, mais ses chiffres se mesurent : le temps
	pour prendre l'allure, la distance d'arret, la hauteur d'un saut, et
	surtout ce que le joueur gagne a sauter en boucle ou a tourner en l'air.
	Le banc pilote le joueur a la place du clavier, par gestes fixes, et
	imprime ce qu'il releve. Deux reglages se comparent ainsi sur les memes
	gestes, et une regression se voit au premier coup d'oeil.

	Console : unholy_moveTest <scenario>. Un nom inconnu liste les scenarios.
	Chaque scenario part du meme endroit, arrete, dans la meme direction : le
	banc y replace le joueur entre deux scenarios.
*/

// Ce que le joueur est devenu apres une image de physique.
struct unholyMoveSample_t
{
	int				time;			// ms
	idVec3			origin;
	idVec3			velocity;
	idVec3			gravityNormal;
	bool			onGround;
	bool			jumped;			// a decolle pendant cette image
	bool			crouching;
	float			eyeHeight;
	float			stamina;		// secondes de course
	int				clip;			// cartouches dans l'arme, -1 sans arme
	int				reserve;		// cartouches en reserve
};

// Ce que le banc demande au joueur pour l'image a venir.
struct unholyMoveDrive_t
{
	int				forward;		// -127 .. 127
	int				right;
	int				buttons;		// BUTTON_RUN, BUTTON_CROUCH, BUTTON_JUMP, BUTTON_ATTACK, BUTTON_ZOOM
	int				impulse;		// une commande a donner a cette image, 0 sinon
	float			yawDelta;		// degres a ajouter au lacet de la vue
	float			pitch;			// inclinaison de la vue a tenir, en degres (vers le bas)
	bool			resetToStart;	// replacer le joueur au depart, arrete
};

struct unholyMoveScenario_t;
struct unholyMoveStep_t;

class UnholyMoveTest
{
public:
					UnholyMoveTest();

	// Demarre le scenario nomme depuis la position donnee. Faux s'il n'existe pas.
	bool			Start( const char* name, int time, const idVec3& origin, float yaw );
	void			Stop();
	bool			IsRunning() const
	{
		return scenario != NULL;
	}

	const idVec3&	StartOrigin() const
	{
		return startOrigin;
	}
	float			StartYaw() const
	{
		return startYaw;
	}

	// Avant la physique : les commandes de l'image.
	void			Drive( int time, int frameMsec, unholyMoveDrive_t& drive );
	// Apres la physique : ce qui s'est passe.
	void			Measure( const unholyMoveSample_t& sample );

	static void		ListScenarios();

private:
	void			BeginScenario( int time );
	void			BeginStep( int time );
	void			EndStep();
	float			ExpectedSpeed() const;

	const unholyMoveScenario_t* const* queue;	// scenarios a enchainer
	int				queueLength;
	int				queueIndex;

	const unholyMoveScenario_t* scenario;
	int				stepIndex;
	int				stepStart;
	int				stepFrame;
	bool			pendingReset;
	int				restUntil;					// pause entre deux scenarios

	idVec3			startOrigin;
	float			startYaw;

	// releves de l'etape en cours
	bool			hasSample;
	unholyMoveSample_t last;
	float			stepStartZ;
	float			maxSpeed;
	float			sumSpeed;
	int				numSpeed;
	float			distance;
	int				reach[3];					// 50, 90 et 99 % de l'allure attendue
	int				stopTime;
	float			stopDistance;
	int				takeoffs;
	int				lastTakeoff;
	int				minTakeoffInterval;
	int				firstTakeoff;
	int				firstLanding;
	float			apex;
	int				eyeReached;
	int				fullSprintEnd;
	int				walkReached;
	int				staminaFull;
	int				clipStart;
	int				reserveStart;
};

#endif /* !__UNHOLY_MOVETEST_H__ */
