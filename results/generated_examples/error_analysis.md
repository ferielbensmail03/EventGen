# Error analysis (automatically selected examples)


## attention_greedy


### repetition - 70.0% of test outputs

- **Input:** type : musique , concert , événement culturel | titre : Journées du Patrimoine - Concert lyrique au Mas de Bombequiols
  - **Reference:** Petite pause musicale entre la visite guidée et la conférence dans le cadre des journées du patrimoine !
  - **Generated:** Concert de l'histoire de l'histoire de l'église de l'église de l'église de l'église de l'église de l'église.
  - ROUGE-L 0.0

- **Input:** type : théâtre , spectacle , événement culturel | titre : Théâtre Le temps qui reste
  - **Reference:** Emma, fraîchement devenue veuve, retrouve ses trois amis d'enfance Paul, Franck et Adrien. Alors que leur peine devrait être immense, ils saisissent ce moment de retrouvailles pour révéler leurs rêves inavouables et leurs envies qui vont être pour le moins... surprenantes.
  - **Generated:** Théâtre théâtre théâtre théâtre " théâtre " théâtre " théâtre "
  - ROUGE-L 0.0

- **Input:** type : conférence , événement culturel | titre : Conférence : Le Hartmannswillerkopf, du champ de bataille au haut lieu de l'amitié franco-allemande
  - **Reference:** Les conférenciers sont Jean KLINKERT et Florian HENSEL
  - **Generated:** Conférence de l'histoire de l', de l', de l',, de l',, de l',, de l',, de l',, de l',, de l'université de la.
  - ROUGE-L 0.0


### too_short - 19.0% of test outputs

- **Input:** type : événement sportif | titre : Fête Halloween aux Thermes
  - **Reference:** A C C È S E S P A C E A Q U A - D É T E N T E E N C A S & B O N B O N S C O N T E S D ' H A L L O W E E N
  - **Generated:** Venez fêter halloween, la fête de la,
  - ROUGE-L 0.0

- **Input:** type : théâtre , spectacle , événement culturel | titre : Théâtre Le temps qui reste
  - **Reference:** Emma, fraîchement devenue veuve, retrouve ses trois amis d'enfance Paul, Franck et Adrien. Alors que leur peine devrait être immense, ils saisissent ce moment de retrouvailles pour révéler leurs rêves inavouables et leurs envies qui vont être pour le moins... surprenantes.
  - **Generated:** Théâtre théâtre théâtre théâtre " théâtre " théâtre " théâtre "
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : SOUS LE SAPIN... LES EMMERDES !
  - **Reference:** Comment le réveillon tranquille d'une famille bourgeoise va être troublé par la venue d'une invitée inattendue... et encombrante.
  - **Generated:** Un spectacle de noël de noël !
  - ROUGE-L 0.0


### no_eos - 5.0% of test outputs

- **Input:** type : vente , marché | titre : Marché des producteurs et créateurs
  - **Reference:** Les 1er et 3ème samedi du mois.
  - **Generated:** Marché de producteurs locaux,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0

- **Input:** type : vente , marché , fête traditionnelle , événement social | titre : Marché de Noël et Saint-Nicolas
  - **Reference:** Venez célébrer la Saint-Nicolas dans une ambiance festive et chaleureuse.
  - **Generated:** Marché de noël de noël de noël, de noël, marché de noël, de noël, de noël,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0

- **Input:** type : vente , marché | titre : Marché local
  - **Reference:** Présence d'une épicerie ambulante avec une étale variée
  - **Generated:** Marché de producteurs et légumes,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0


### missing_title_info - 41.7% of test outputs

- **Input:** type : théâtre , spectacle , événement culturel | titre : Théâtre - 7 Minutes comité d'usine par la Cie Théâtr'ou vers
  - **Reference:** Blanche est déléguée du comité d'usine. Elle doit parlementer avec les nouveaux propriétaires de son entreprise sur les conditions de reprise de leur lieu de travail.
  - **Generated:** Une soirée,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0

- **Input:** type : vente , marché | titre : Les Marchés de La Grand Combe
  - **Reference:** Les marchés ont lieu les mercredis et les samedis matins.
  - **Generated:** Le marché de la, de la, de la, de la, de la, de la, de la,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par le club Ping Pong Varennois
  - **Generated:** Venez nombreux à la salle des fêtes de la.
  - ROUGE-L 0.0


### unk_heavy_ref - 7.8% of test outputs

- **Input:** type : musique , concert , événement culturel | titre : GOSPEL - Fabienne Della-Moniqua et ses Chorales
  - **Reference:** FABIENNE DELLA - MONICA / HAPPYPHONIE / IMANI VOICES / ISSOIRE EN CHOEUR
  - **Generated:** Le festival de la de la, vous invite à un concert festif et festif et festif et de.
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par le club Ping Pong Varennois
  - **Generated:** Venez nombreux à la salle des fêtes de la.
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par l'Amicale Gymnique Varennoise le samedi 7 novembre
  - **Generated:** Venez nombreux à la salle des fêtes de la.
  - ROUGE-L 0.0


### generic - 8.5% of test outputs

- **Input:** type : vente , marché | titre : Marché local
  - **Reference:** Présence d'une épicerie ambulante avec une étale variée
  - **Generated:** Marché de producteurs et légumes,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par l'Amicale Gymnique Varennoise le samedi 7 novembre
  - **Generated:** Venez nombreux à la salle des fêtes de la.
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par l'Union sportive Trézelloise !
  - **Generated:** Venez nombreux à la salle des fêtes de la.
  - ROUGE-L 0.0


### best examples (highest ROUGE-L)

- **Input:** type : compétition sportive , événement sportif | titre : VOLLEY-BALL - BÉZIERS ANGELS / NANTES
  - **Reference:** Les Béziers Angels reçoivent à domicile Nantes.
  - **Generated:** Les béziers angels reçoivent à domicile.
  - ROUGE-L 93.3

- **Input:** type : non précisé | titre : C'est quoi ton entreprise 2026 ? L'Atelier Insolite
  - **Reference:** C'est quoi ton entreprise ? Découvrez l'envers du décor d'un fabriquant de chaussures
  - **Generated:** C'est quoi ton entreprise ? Découvrez l'envers du décor d'un entreprise de
  - ROUGE-L 90.3

- **Input:** type : non précisé | titre : C'est quoi ton entreprise 2026 ? Brasserie Bigorneau
  - **Reference:** C'est quoi ton entreprise ? découvrez l'envers du décor d'une brasserie.
  - **Generated:** C'est quoi ton entreprise ? Découvrez l'envers du décor d'un entreprise de cosmétiques et cosmétiques.
  - ROUGE-L 76.5


## baseline_greedy


### repetition - 58.3% of test outputs

- **Input:** type : non précisé | titre : Laurent Gerra se met à table !
  - **Reference:** Laurent Gerra "se met à table" ! Un nouveau one man show de l'artiste au Silo Marseille ! Nouveau spectacle à savourer.
  - **Generated:** C'est quoi ton entreprise ? C'est quoi ton entreprise ?
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Micro Folie - Jeu vidéo Discovery Tour L'ère Vinking
  - **Reference:** Micro-Folie - Jeu vidéo Discovery Tour L'ère Viking
  - **Generated:** Le samedi 31 octobre, la médiathèque de la médiathèque de la médiathèque de la à la de de la à la médiathèque de la.
  - ROUGE-L 0.0

- **Input:** type : théâtre , spectacle , événement culturel | titre : L'Olympiade des Pitchouns fête Halloween à Saint-Andiol
  - **Reference:** L'association L'Olympiade des Pitchouns fête Halloween
  - **Generated:** Petits et grands, sorcières, créatures fantastiques et créatures fantastiques et de et de,,,,,,,,,,,,,,,,,,,,,, et de.
  - ROUGE-L 0.0


### too_short - 15.5% of test outputs

- **Input:** type : non précisé | titre : Laurent Gerra se met à table !
  - **Reference:** Laurent Gerra "se met à table" ! Un nouveau one man show de l'artiste au Silo Marseille ! Nouveau spectacle à savourer.
  - **Generated:** C'est quoi ton entreprise ? C'est quoi ton entreprise ?
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : SOIRÉE CONVIVIALE AVEC AU MENU COUSCOUS MAISON
  - **Reference:** Jeudi 5 novembre à 20h salle polyvalente d'Avène Repas convivial organisé par le Foyer rural d'Avène Tarif : 15€ non adhérents / 13€ adhérents / 10€ enfants (-12 ans) Inscriptions au Menu : charcuterie-salade Couscous Fromage Flan Vin / café compris
  - **Generated:** Soirée de la,, et de la de la de la de la de la de la de la de la.
  - ROUGE-L 0.0

- **Input:** type : animation locale , événement social | titre : Soirée Blind Test
  - **Reference:** Soirée Blind Test organisée par l'association Energie Musicale le 21 novembre à la salle du Foyer Soleil à Apremont.
  - **Generated:** Venez passer un moment convivial et convivial et de !
  - ROUGE-L 0.0


### no_eos - 5.6% of test outputs

- **Input:** type : vente , foire ou salon | titre : Forum avenir étudiant
  - **Reference:** Le forum Avenir étudiant réunira environ 100 partenaires pour répondes à toutes vos questions concernant l'orientation, les formations de l'enseignement supérieur et la vie étudiante. De nombreuses écoles et universités de l'académie Nancy-Metz viendront présenter leurs filières de formation.
  - **Generated:** _ * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  - ROUGE-L 0.0

- **Input:** type : vente , marché | titre : Marché des producteurs et créateurs
  - **Reference:** Les 1er et 3ème samedi du mois.
  - **Generated:** Marché de producteurs locaux, producteurs locaux, de,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0

- **Input:** type : vente , foire ou salon , événement culturel | titre : Epoqu'Auto
  - **Reference:** Comme chaque année, le rendez-vous lyonnais des amoureux d'automobiles et motos anciennes revient pour à une déambulation dans l'histoire à travers l'évolution de l'automobile.
  - **Generated:** La - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  - ROUGE-L 0.0


### missing_title_info - 51.5% of test outputs

- **Input:** type : théâtre , spectacle , événement culturel | titre : Un ado peut en cacher un autre
  - **Reference:** Une comédie familiale et satirique sur les générations
  - **Generated:** Dans un cadre de la,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Laurent Gerra se met à table !
  - **Reference:** Laurent Gerra "se met à table" ! Un nouveau one man show de l'artiste au Silo Marseille ! Nouveau spectacle à savourer.
  - **Generated:** C'est quoi ton entreprise ? C'est quoi ton entreprise ?
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Micro Folie - Jeu vidéo Discovery Tour L'ère Vinking
  - **Reference:** Micro-Folie - Jeu vidéo Discovery Tour L'ère Viking
  - **Generated:** Le samedi 31 octobre, la médiathèque de la médiathèque de la médiathèque de la à la de de la à la médiathèque de la.
  - ROUGE-L 0.0


### unk_heavy_ref - 7.8% of test outputs

- **Input:** type : musique , concert , événement culturel | titre : GOSPEL - Fabienne Della-Moniqua et ses Chorales
  - **Reference:** FABIENNE DELLA - MONICA / HAPPYPHONIE / IMANI VOICES / ISSOIRE EN CHOEUR
  - **Generated:** Concert de la musique, la musique, la musique de la musique et de la musique.
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par le club Ping Pong Varennois
  - **Generated:** Venez nombreux à la salle des fêtes de la salle des fêtes de la.
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par l'Amicale Gymnique Varennoise le samedi 7 novembre
  - **Generated:** Venez nombreux à la salle des fêtes de la salle des fêtes de la.
  - ROUGE-L 0.0


### generic - 6.9% of test outputs

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par le club Ping Pong Varennois
  - **Generated:** Venez nombreux à la salle des fêtes de la salle des fêtes de la.
  - ROUGE-L 0.0

- **Input:** type : vente , marché | titre : Marché local
  - **Reference:** Présence d'une épicerie ambulante avec une étale variée
  - **Generated:** Marché marché de producteurs locaux, locaux, produits locaux,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,...
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par l'Union sportive Trézelloise !
  - **Generated:** Venez nombreux à la salle des fêtes de la salle des fêtes de la.
  - ROUGE-L 0.0


### best examples (highest ROUGE-L)

- **Input:** type : compétition sportive , événement sportif | titre : VOLLEY-BALL - BÉZIERS ANGELS / NANTES
  - **Reference:** Les Béziers Angels reçoivent à domicile Nantes.
  - **Generated:** La béziers angels reçoivent à domicile la france.
  - ROUGE-L 70.6

- **Input:** type : vente , marché | titre : Marché de Produits Manufacturés Ambroise Courtois
  - **Reference:** Produits vendus : vêtements, chaussures, sacs, bazar, etc. 30 commerçants.
  - **Generated:** Produits vendus : fruits et légumes, chaussures, sacs, bazar,
  - ROUGE-L 69.0

- **Input:** type : théâtre , spectacle , événement culturel | titre : La Baleine : théâtre " The Loop"
  - **Reference:** La Baleine vous propose la pièce de théâtre " The Loop ".
  - **Generated:** Le baleine vous propose une séance de théâtre " théâtre ".
  - ROUGE-L 64.0


## attention_beam


### repetition - 42.7% of test outputs

- **Input:** type : événement sportif | titre : Randonnée groupe : Entre Marche et Bourbonnais (Lamaids)
  - **Reference:** Ce parcours de randonnée est proposé par l'association "Les mille pattes Genestois".
  - **Generated:** Rando vtt : rando vtt : rando vtt : rando vtt)
  - ROUGE-L 0.0

- **Input:** type : musique , jeune public , concert , événement culturel | titre : Concert de l'Harmonie de Bonny avec la chorale "Nuances"
  - **Reference:** La chorale Nuances invite 3 autres chorales pour un naprès-midi musicale inoubliable. Rendez-vous le dimanche 08 mars à 15h à la salle des fêtes. Entrée libre !
  - **Generated:** Concert de l'harmonie de l'école municipale de l'école municipale de
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : ATELIER 0 DÉCHET "FABRIQUER SES BORDURES NATURELLES"
  - **Reference:** Délimiter ses espaces dans le jardin avec une bordure esthétique tout en recyclant les déchets du jardin, c'est possible !
  - **Generated:** Un atelier créatif pour un atelier créatif pour créer un moment créatif et créatif pour créer un moment créatif et
  - ROUGE-L 0.0


### too_short - 44.9% of test outputs

- **Input:** type : non précisé | titre : Journées du Patrimoine - Visite patrimoine du village médiéval
  - **Reference:** L'association Sauvegarde de Saint-Étienne vous propose une visite commentée de l'église et de ses vestiges médiévaux.
  - **Generated:** Dans le cadre des journées européennes du patrimoine,
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : LUGE SUR RAIL DRACO'SNOW
  - **Reference:** LUGE SUR RAIL Ouvert tous les jours du 17 octobre au 31 octobre De 10H à 13H et de 13H30 à 18H 8.50€ Adulte / 7.50€ Enfant Venez découvrir la luge à sensations de Pyrénées 2000
  - **Generated:** Une soirée d'une soirée d'un évènement sportif !
  - ROUGE-L 0.0

- **Input:** type : théâtre , événement culturel | titre : PASSAGE(S) : Lecture théâtralisée
  - **Reference:** Lecture théâtralisée par les écrivants de l'atelier d'écriture de l'Autre Scène, orchestrée par Marion Bouquet. Tout public à partir de 10 ans
  - **Generated:** Dans le cadre du festival " la compagnie " la compagnie "
  - ROUGE-L 0.0


### no_eos - 0.4% of test outputs

- **Input:** type : musique , concert , événement culturel | titre : CONCERT : Soirée New Jazz Club : Volubilis - La Lune des Pirates
  - **Reference:** Soirée New Jazz Club : Volubilis En partenariat avec La Maison de la Culture d'Amiens VEN.
  - **Generated:** Concert jazz blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues, blues,
  - ROUGE-L 2.6

- **Input:** type : non précisé | titre : FESTI' BIERES 2022
  - **Reference:** Festi' Lens vous propose une fête de la bière !
  - **Generated:** L'association ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  - ROUGE-L 2.8

- **Input:** type : musique , concert , spectacle , événement culturel | titre : Festi'Cuivre - concert du duo Madame Doug
  - **Reference:** Concert du duo Madame Doug en ouverture du Festival FESTI'CUIVRES. Réservations auprès de l'ACDIM.
  - **Generated:** Venez découvrir l'univers de l'univers de la musique, de la musique, de la musique, de la,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
  - ROUGE-L 5.1


### missing_title_info - 44.3% of test outputs

- **Input:** type : non précisé | titre : Justine Jérémie, de Montmartre à Murles
  - **Reference:** Une parenthèse cabaret où la chanson française retrouve toute sa poésie.
  - **Generated:** Un voyage musical à l'espace julien marseille !
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Les journées archi-ludiques
  - **Reference:** Les journées archi-ludiques font leur grand retour !
  - **Generated:** Le le cadre du festival ar (2005)
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Projection photos
  - **Reference:** Premier regard photographique sur la population d'Etaples-sur-mer
  - **Generated:** Dans le cadre du festival alimenterre ", "
  - ROUGE-L 0.0


### unk_heavy_ref - 7.8% of test outputs

- **Input:** type : musique , concert , événement culturel | titre : GOSPEL - Fabienne Della-Moniqua et ses Chorales
  - **Reference:** FABIENNE DELLA - MONICA / HAPPYPHONIE / IMANI VOICES / ISSOIRE EN CHOEUR
  - **Generated:** L'association des orgues vous invite à un concert festif et festif au profit de l'avent.
  - ROUGE-L 0.0

- **Input:** type : conférence , événement culturel | titre : Conférence | Frontières et souveraineté
  - **Reference:** Par Patrick Debaere, commissaire divisionnaire honoraire (coopération policière européenne)
  - **Generated:** La société de l'art et de l'économie locale.
  - ROUGE-L 0.0

- **Input:** type : vente , marché | titre : Marché local
  - **Reference:** Présence d'une épicerie ambulante avec une étale variée
  - **Generated:** Tous les mercredis matin, la place de la mairie.
  - ROUGE-L 0.0


### generic - 8.7% of test outputs

- **Input:** type : vente , marché | titre : Marché local
  - **Reference:** Présence d'une épicerie ambulante avec une étale variée
  - **Generated:** Tous les mercredis matin, la place de la mairie.
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Fête Halloween aux Thermes
  - **Reference:** A C C È S E S P A C E A Q U A - D É T E N T E E N C A S & B O N B O N S C O N T E S D ' H A L L O W E E N
  - **Generated:** Venez fêter halloween à l'occasion d'halloween !
  - ROUGE-L 0.0

- **Input:** type : musique , concert , événement culturel | titre : Peet
  - **Reference:** Peet arrive au Makeda le 13 novembre !
  - **Generated:** Un concert de de la, de la, de la, de la.
  - ROUGE-L 0.0


### best examples (highest ROUGE-L)

- **Input:** type : compétition sportive , événement sportif | titre : VOLLEY-BALL - BÉZIERS ANGELS / NANTES
  - **Reference:** Les Béziers Angels reçoivent à domicile Nantes.
  - **Generated:** Les béziers angels reçoivent à domicile mulhouse.
  - ROUGE-L 87.5

- **Input:** type : vente , marché | titre : Marché de Produits Manufacturés Ambroise Courtois
  - **Reference:** Produits vendus : vêtements, chaussures, sacs, bazar, etc. 30 commerçants.
  - **Generated:** Produits vendus : vêtements, chaussures, sacs, bazar.
  - ROUGE-L 81.5

- **Input:** type : événement sportif | titre : Loto
  - **Reference:** Loto organisé par le Comité des fêtes de Trézelles !
  - **Generated:** Loto organisé par le comité des fêtes.
  - ROUGE-L 77.8


## baseline_beam


### repetition - 36.4% of test outputs

- **Input:** type : théâtre , spectacle , événement culturel | titre : L'Olympiade des Pitchouns fête Halloween à Saint-Andiol
  - **Reference:** L'association L'Olympiade des Pitchouns fête Halloween
  - **Generated:** Petits et grands, sorcières, petits et grands !
  - ROUGE-L 0.0

- **Input:** type : événement sportif | titre : Randonnées bimensuelles
  - **Reference:** Licence FFRandonnée obligatoire Possibilité d'adhérer via le site
  - **Generated:** Randonnée pédestre de la km, la randonnée pédestre de l'association de la.
  - ROUGE-L 0.0

- **Input:** type : cinéma , projection , lieu de loisirs , événement professionnel , événement culturel | titre : Ciné-Débat
  - **Reference:** Présentation et débat avec Clémentine Defois Brandeis, mé diatrice en archéologie et histoire.
  - **Generated:** Projection du film " le film " " " le film " le film "
  - ROUGE-L 0.0


### too_short - 40.3% of test outputs

- **Input:** type : événement culturel | titre : ATELIER MACRAMÉ
  - **Reference:** Découvrez les bases du macramé, à travers quelques noeuds simples et accessibles à tous. Lors de cet atelier, vous réalisez un porte-clés personnalisé (octobre) ou un petit sapin (novembre), en macramé. Un moment créatif, idéal pour s'initier à cet art du fil.
  - **Generated:** C'est quoi ton entreprise ?
  - ROUGE-L 0.0

- **Input:** type : conférence , événement culturel , événement sportif | titre : Pas à pas vers la maternelle
  - **Reference:** Le centre socio culturel Arc-en-ciel vous propose un nouveau programme de découverte pour les enfants et leurs parents pour: favoriser l'intégration en maternelle & aider au développement et à la sociabilisation.
  - **Generated:** C'est quoi ton entreprise ?
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : VISITE COMMENTÉE DE BALARUC-LES-BAINS AVEC DIVERS UNI VERS
  - **Reference:** Divers Uni Vers vous invite à plonger dans le passé de Balaruc-les-Bains à travers sa visite commentée "Histoires thermales et mythologie".
  - **Generated:** C'est quoi ton entreprise !
  - ROUGE-L 0.0


### no_eos - 0.4% of test outputs

- **Input:** type : vente , foire ou salon | titre : Forum avenir étudiant
  - **Reference:** Le forum Avenir étudiant réunira environ 100 partenaires pour répondes à toutes vos questions concernant l'orientation, les formations de l'enseignement supérieur et la vie étudiante. De nombreuses écoles et universités de l'académie Nancy-Metz viendront présenter leurs filières de formation.
  - **Generated:** _ * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Les caricatures de Fabrice
  - **Reference:** Fab' dessine depuis son plus jeune âge.
  - **Generated:** Après le succès de la tournée de l'amphithéâtre de rodez - théâtre de la carrosserie mesnier 3 rue de dieu, saint-amand-montrond théâtre de théâtre, saint-amand-montrond théâtre de théâtre de la carrosserie mesnier 3 rue de dieu, saint-amand-montrond théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - - - - - - - -
  - ROUGE-L 0.0

- **Input:** type : théâtre , événement culturel | titre : LA MAISON AUX LAPINS
  - **Reference:** Un voyage d'une rare intensité. Une histoire qui laisse une empreinte.
  - **Generated:** Théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre - théâtre -
  - ROUGE-L 0.0


### missing_title_info - 50.7% of test outputs

- **Input:** type : non précisé | titre : ANNULE - Sunset espagnol - Mas Bruguière
  - **Reference:** Une soirée aux accents espagnols face au coucher du soleil, entre saveurs méditerranéennes et rythmes flamenco.
  - **Generated:** C'est quoi ton entreprise !
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Causs en Oc' - Fête Occitane
  - **Reference:** Une soirée pour danser, chanter et célébrer la culture occitane dans toute sa diversité !
  - **Generated:** Annulation de par le comité des fêtes de
  - ROUGE-L 0.0

- **Input:** type : musique , concert , événement culturel | titre : Sandrine Piau et Trio Wanderer
  - **Reference:** Et si Beethoven était le guide spirituel que le monde désorienté attendait ?
  - **Generated:** Concert de l'opéra de l'opéra de picardie
  - ROUGE-L 0.0


### unk_heavy_ref - 7.8% of test outputs

- **Input:** type : musique , concert , événement culturel | titre : GOSPEL - Fabienne Della-Moniqua et ses Chorales
  - **Reference:** FABIENNE DELLA - MONICA / HAPPYPHONIE / IMANI VOICES / ISSOIRE EN CHOEUR
  - **Generated:** Concert de la musique de l'association de l'école de
  - ROUGE-L 0.0

- **Input:** type : vente , marché | titre : Marché local
  - **Reference:** Présence d'une épicerie ambulante avec une étale variée
  - **Generated:** Petit marché de producteurs locaux et producteurs locaux.
  - ROUGE-L 0.0

- **Input:** type : événement culturel , événement sportif | titre : Cinéma : soirée Japan horror - Ring d'Hideo Nakata
  - **Reference:** Ring (1998) 1h36 - vost Interdit aux -12 ans Réalisé par Hideo Nakata Avec Nanako Matsushima, Miki Nakatani, Hiroyuki Sanada Japon / horreur
  - **Generated:** Le ciné planète propose une nouvelle édition du film " le cinéma " le cinéma "
  - ROUGE-L 0.0


### generic - 8.1% of test outputs

- **Input:** type : vente , marché | titre : Marché local
  - **Reference:** Présence d'une épicerie ambulante avec une étale variée
  - **Generated:** Petit marché de producteurs locaux et producteurs locaux.
  - ROUGE-L 0.0

- **Input:** type : non précisé | titre : Fanzone Lidl-Trek
  - **Reference:** Lidl France derrière les coureurs Lidl Trek !
  - **Generated:** Un spectacle de,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,, et de..
  - ROUGE-L 0.0

- **Input:** type : vente , marché | titre : Festival "Vive Noël !"
  - **Reference:** Quatre samedis d'Avent à Neuviller-la-Roche, puis une randonnée nocturne sur les traces des Rois mages : taverne éphémère, créateurs locaux, chorale itinérante, calendrier mystère, saint Nicolas, flambeaux et lanternes, pentathlon, réveillon surprise.
  - **Generated:** Plongez dans la magie des fêtes de noël !
  - ROUGE-L 3.9


### best examples (highest ROUGE-L)

- **Input:** type : non précisé | titre : C'est quoi ton entreprise 2026 ? Brasserie Bigorneau
  - **Reference:** C'est quoi ton entreprise ? découvrez l'envers du décor d'une brasserie.
  - **Generated:** C'est quoi ton entreprise ? Découvrez l'envers du décor d'une métallerie.
  - ROUGE-L 93.3

- **Input:** type : non précisé | titre : C'est quoi ton entreprise 2026 ? Prostyl
  - **Reference:** C'est quoi ton entreprise ? Découvrez l'envers du décor d'une menuiserie
  - **Generated:** C'est quoi ton entreprise ? Découvrez l'envers du décor d'une métallerie.
  - ROUGE-L 89.7

- **Input:** type : non précisé | titre : C'est quoi ton entreprise 2026 ? ALISE
  - **Reference:** C'est quoi ton entreprise ? découvrez l'envers du décor d'une entreprise solidaire
  - **Generated:** C'est quoi ton entreprise ? Découvrez l'envers du décor d'une métallerie.
  - ROUGE-L 86.7
