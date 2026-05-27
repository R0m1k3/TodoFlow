# Task: Centralized Todo List (Widget Windows & API Docker)

## Contexte
Développement d'un widget Windows moderne et simple connecté à un serveur centralisé hébergé dans un conteneur Docker. L'API du serveur doit être accessible par un agent IA pour piloter la liste de tâches. Les tâches doivent afficher leur date de création et pouvoir être marquées comme "En cours" ou "Terminé".

## Focus Actuel
- Projet entièrement à jour et documenté pour les Agents IA externes.

## Master Plan
- [x] **Synchronisation avec le Dépôt Distant**
  - [x] Mettre à jour `task.md` pour refléter la demande de l'utilisateur
  - [x] Effectuer un `git pull` pour appliquer les 20 commits de retard sur `origin/main`
  - [x] Valider l'état des fichiers locaux et s'assurer que la copie locale est propre et fonctionnelle
- [x] **Phase 6 : Mise à Jour de la Documentation pour Agent IA Externe (README)**
  - [x] Concevoir le plan d'action simplifié (`implementation_plan.md`)
  - [x] Documenter la route manquante `GET /api/v1/tasks/{task_id}` dans `README_AI_AGENT.md`
  - [x] Ajouter les schémas d'outils (Function Calling) pour LLMs dans `README_AI_AGENT.md`
  - [x] Vérifier la cohérence de la documentation avec le code réel de l'API
- [x] **Phase 1 : Conception & Architecture**
  - [x] Créer le fichier `task.md`
  - [x] Consulter le sous-agent `architecte` pour la structure de l'API et du conteneur
  - [x] Consulter le sous-agent `web_designer` pour le design visuel et l'expérience utilisateur
  - [x] Générer la preview visuelle (image maquette) du widget
  - [x] Rédiger l'architecture technique détaillée dans `implementation_plan.md`
  - [x] Soumettre le plan à l'utilisateur pour approbation et intégrer ses retours
- [x] **Phase 2 : Développement du Serveur API (Docker)**
  - [x] Initialiser le projet serveur (FastAPI / SQLite / Docker)
  - [x] Implémenter la base de données et les modèles (Todo: id, title, status, created_at, updated_at)
  - [x] Créer les endpoints API (CRUD, gestion des statuts, documentation OpenAPI/Swagger pour l'IA)
  - [x] Configurer le Dockerfile et docker-compose
  - [x] Valider l'API localement avec des tests
- [x] **Phase 3 : Développement du Widget Windows (Tauri/HTML/CSS/JS)**
  - [x] Initialiser le projet de widget (Tauri + Vanilla HTML/CSS/JS)
  - [x] Créer le design système CSS (Glassmorphism, animations, thèmes)
  - [x] Développer l'interface utilisateur du widget
    - [x] Liste des tâches et toggle de statut
    - [x] Création directe de tâches depuis le widget
    - [x] Section configuration (URL de l'API, mode "Toujours au premier plan", clé API)
  - [x] Connecter le widget à l'API via l'URL configurée
  - [x] Configurer la fenêtre Tauri (sans bordure, positionnable, intégration système, option premier plan native)
  - [x] Configurer le démarrage automatique de l'application avec Windows
- [x] **Phase 4 : Intégration IA & Sécurité**
  - [x] Ajouter une authentification par clé API simple
  - [x] Rédiger un guide d'intégration pour l'agent IA (schéma OpenAPI)
- [x] **Phase 5 : Tests & Validation**
  - [x] Tester la synchronisation multi-ordinateurs
  - [x] Valider la compatibilité avec un agent IA
  - [x] Rédiger le rapport de fin (`walkthrough.md`)

## Journal de Progression
- **2026-05-26** : Plan validé par l'utilisateur. Ajout des spécifications : configuration de l'URL API dans le widget, création directe de tâches, mode toujours au premier plan, et démarrage automatique. Début du développement du serveur API.
- **2026-05-26** : Implémentation du serveur API conteneurisé (FastAPI + SQLModel + Docker Compose) et du widget de bureau Tauri (HTML/CSS/JS, drag-region, always-on-top natif, autostart registre Windows, tray icon). Rédaction des tests unitaires et du guide d'intégration pour Agent IA. Début de la validation.
- **2026-05-27** : Récupération des dernières modifications du dépôt distant (`origin/main`). Synchronisation de 20 commits incluant des améliorations de l'interface (style glassmorphic, redimensionnement natif, icônes premium 3D) et des correctifs pour l'intégration Docker/Tauri. La copie locale est désormais à jour.
- **2026-05-27** : Mise à jour complète du guide d'intégration `README_AI_AGENT.md`. Ajout de la documentation pour la route `GET /api/v1/tasks/{task_id}` et création de schémas complets d'outils (Function Calling / Tools) pour OpenAI, Gemini et Anthropic Claude pour faciliter l'intégration immédiate d'un agent externe.
