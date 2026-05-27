# 🤖 Guide d'Intégration pour Agent IA - TodoFlow API

Ce guide explique comment un **Agent d'Intelligence Artificielle** (comme un assistant autonome, un agent de codage ou un script LLM) peut se connecter, comprendre et piloter la Todo List centralisée de l'utilisateur.

---

## 🔑 1. Authentification & Sécurité

Pour toutes les requêtes HTTP, l'Agent IA doit s'authentifier en fournissant la clé API configurée dans l'en-tête `X-API-Key`.

### En-tête HTTP Requis :
```http
X-API-Key: ai-agent-token-secure-101
```

*Note : La clé par défaut pour l'agent IA dans la configuration de production est `ai-agent-token-secure-101`, mais elle peut être personnalisée via la variable d'environnement `API_KEYS_RAW` du conteneur Docker.*

---

## 📐 2. Découverte Automatique (OpenAPI / Swagger)

L'API TodoFlow a été conçue avec **FastAPI**, ce qui signifie qu'elle génère dynamiquement une spécification OpenAPI standard au format JSON.

### Endpoints de Découverte :
*   **Schéma OpenAPI JSON :** `http://<IP_SERVEUR>:8000/openapi.json`
    *(Idéal pour qu'un LLM lise et comprenne la structure des données et des routes de manière autonome)*
*   **Documentation Swagger Interactive :** `http://<IP_SERVEUR>:8000/docs`

---

## 📋 3. Spécifications des Opérations (CRUD)

### A. Récupérer toutes les tâches (GET `/api/v1/tasks`)
Permet à l'Agent IA de lire la liste de tâches actuelle. Il peut filtrer les tâches par statut.

*   **Query Parameters (Optionnel) :**
    *   `status` : Peut être `"A faire"`, `"En cours"` ou `"Termine"`.
*   **Réponse (200 OK) :** Une liste d'objets au format suivant :
    ```json
    [
      {
        "id": "e1a77ff0-2c32-4f37-baef-e68b903f806e",
        "title": "Acheter du pain",
        "description": null,
        "status": "A faire",
        "created_at": "2026-05-26T14:15:30Z",
        "updated_at": "2026-05-26T14:15:30Z"
      }
    ]
    ```

### B. Créer une nouvelle tâche (POST `/api/v1/tasks`)
Permet à l'Agent IA d'ajouter un nouvel objectif pour l'utilisateur.

*   **Request Body (JSON) :**
    ```json
    {
      "title": "Préparer la réunion de projet",
      "description": "Rédiger l'ordre du jour et préparer les diapositives",
      "status": "A faire"
    }
    ```
*   **Réponse (201 Created) :** Renvoie l'objet créé avec son UUID unique généré par le serveur et son horodatage de création (`created_at`).

### C. Récupérer les détails d'une tâche (GET `/api/v1/tasks/{id}`)
Permet à l'Agent IA d'obtenir les informations complètes d'une tâche spécifique à partir de son UUID.

*   **Réponse (200 OK) :**
    ```json
    {
      "id": "e1a77ff0-2c32-4f37-baef-e68b903f806e",
      "title": "Acheter du pain",
      "description": "Prendre une tradition bien cuite",
      "status": "A faire",
      "created_at": "2026-05-26T14:15:30Z",
      "updated_at": "2026-05-26T14:15:30Z"
    }
    ```
*   **Réponse (404 Not Found) :** Si aucune tâche ne correspond à l'identifiant fourni.

### D. Mettre à jour une tâche (PUT `/api/v1/tasks/{id}`)
Permet à l'Agent IA de marquer une tâche comme **"En cours"** ou **"Termine"**, ou d'en modifier le titre/description.

*   **Request Body (JSON - Mise à jour partielle acceptée) :**
    ```json
    {
      "status": "En cours"
    }
    ```
*   **Réponse (200 OK) :** Renvoie l'objet mis à jour avec son nouvel horodatage `updated_at`.

### E. Supprimer une tâche (DELETE `/api/v1/tasks/{id}`)
Permet à l'Agent IA de nettoyer la liste en supprimant une tâche.

*   **Réponse (204 No Content) :** Succès de la suppression (aucun corps de réponse).

---

## 🐍 4. Exemple d'implémentation en Python pour l'Agent IA

Voici un script simple montrant comment un Agent IA peut interagir avec l'API en utilisant la bibliothèque `requests` :

```python
import requests

API_URL = "http://localhost:8000/api/v1"
API_KEY = "ai-agent-token-secure-101"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 1. Lire toutes les tâches actives
response = requests.get(f"{API_URL}/tasks", headers=headers)
if response.status_code == 200:
    tasks = response.json()
    print(f"L'utilisateur a {len(tasks)} tâches au total.")

# 2. Créer une nouvelle tâche pour l'utilisateur
new_task = {
    "title": "Analyser les performances de la stack",
    "description": "Tâche générée automatiquement par l'Agent IA",
    "status": "A faire"
}
create_resp = requests.post(f"{API_URL}/tasks", json=new_task, headers=headers)
if create_resp.status_code == 201:
    created_task = create_resp.json()
    task_id = created_task["id"]
    print(f"Tâche créée par l'IA avec succès ! ID: {task_id}")

    # 3. Passer cette tâche "En cours"
    update_resp = requests.put(
        f"{API_URL}/tasks/{task_id}", 
        json={"status": "En cours"}, 
        headers=headers
    )
    if update_resp.status_code == 200:
        print("La tâche a été marquée 'En cours' par l'IA.")
```

---

## 🛠️ 5. Définition des Outils pour Agents IA (Function Calling)

Si vous configurez un agent IA externe utilisant les API d'OpenAI, Anthropic ou Gemini, vous pouvez copier-coller les schémas de fonctions ci-dessous pour lui donner un accès direct et natif à la Todo List.

### A. Format OpenAI / Gemini (JSON Schema)

```json
[
  {
    "type": "function",
    "function": {
      "name": "get_tasks",
      "description": "Récupère la liste de toutes les tâches stockées dans TodoFlow. Permet de filtrer optionnellement par statut.",
      "parameters": {
        "type": "object",
        "properties": {
          "status": {
            "type": "string",
            "enum": ["A faire", "En cours", "Termine"],
            "description": "Filtre optionnel pour récupérer uniquement les tâches ayant ce statut ('A faire', 'En cours', 'Termine')."
          }
        }
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_task",
      "description": "Récupère les détails précis d'une tâche existante à partir de son UUID.",
      "parameters": {
        "type": "object",
        "properties": {
          "task_id": {
            "type": "string",
            "format": "uuid",
            "description": "L'UUID unique de la tâche à récupérer."
          }
        },
        "required": ["task_id"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "create_task",
      "description": "Crée une nouvelle tâche dans la Todo list.",
      "parameters": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "description": "Le titre court et descriptif de la tâche (ex: 'Acheter du pain')."
          },
          "description": {
            "type": "string",
            "description": "Description détaillée de la tâche ou consignes supplémentaires."
          },
          "status": {
            "type": "string",
            "enum": ["A faire", "En cours", "Termine"],
            "default": "A faire",
            "description": "Le statut initial de la tâche (par défaut 'A faire')."
          }
        },
        "required": ["title"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "update_task",
      "description": "Met à jour une tâche existante (modifier le titre, la description, ou changer de statut comme passer à 'En cours' ou 'Termine').",
      "parameters": {
        "type": "object",
        "properties": {
          "task_id": {
            "type": "string",
            "format": "uuid",
            "description": "L'UUID unique de la tâche à modifier."
          },
          "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "description": "Nouveau titre pour la tâche."
          },
          "description": {
            "type": "string",
            "description": "Nouvelle description pour la tâche."
          },
          "status": {
            "type": "string",
            "enum": ["A faire", "En cours", "Termine"],
            "description": "Nouveau statut pour la tâche."
          }
        },
        "required": ["task_id"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "delete_task",
      "description": "Supprime définitivement une tâche de la liste à partir de son UUID.",
      "parameters": {
        "type": "object",
        "properties": {
          "task_id": {
            "type": "string",
            "format": "uuid",
            "description": "L'UUID unique de la tâche à supprimer."
          }
        },
        "required": ["task_id"]
      }
    }
  }
]
```

### B. Format Anthropic / Claude (Messages API Tools)

```json
[
  {
    "name": "get_tasks",
    "description": "Récupère la liste de toutes les tâches stockées dans TodoFlow. Permet de filtrer optionnellement par statut.",
    "input_schema": {
      "type": "object",
      "properties": {
        "status": {
          "type": "string",
          "enum": ["A faire", "En cours", "Termine"],
          "description": "Filtre optionnel pour récupérer uniquement les tâches ayant ce statut."
        }
      }
    }
  },
  {
    "name": "get_task",
    "description": "Récupère les détails précis d'une tâche existante à partir de son UUID.",
    "input_schema": {
      "type": "object",
      "properties": {
        "task_id": {
          "type": "string",
          "format": "uuid",
          "description": "L'UUID unique de la tâche à récupérer."
        }
      },
      "required": ["task_id"]
    }
  },
  {
    "name": "create_task",
    "description": "Crée une nouvelle tâche dans la Todo list.",
    "input_schema": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Le titre court et descriptif de la tâche."
        },
        "description": {
          "type": "string",
          "description": "Description détaillée de la tâche."
        },
        "status": {
          "type": "string",
          "enum": ["A faire", "En cours", "Termine"],
          "default": "A faire",
          "description": "Le statut initial de la tâche."
        }
      },
      "required": ["title"]
    }
  },
  {
    "name": "update_task",
    "description": "Met à jour une tâche existante par son UUID (modifier le titre, la description, ou changer de statut).",
    "input_schema": {
      "type": "object",
      "properties": {
        "task_id": {
          "type": "string",
          "format": "uuid",
          "description": "L'UUID unique de la tâche à modifier."
        },
        "title": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Nouveau titre pour la tâche."
        },
        "description": {
          "type": "string",
          "description": "Nouvelle description."
        },
        "status": {
          "type": "string",
          "enum": ["A faire", "En cours", "Termine"],
          "description": "Nouveau statut."
        }
      },
      "required": ["task_id"]
    }
  },
  {
    "name": "delete_task",
    "description": "Supprime définitivement une tâche de la liste à partir de son UUID.",
    "input_schema": {
      "type": "object",
      "properties": {
        "task_id": {
          "type": "string",
          "format": "uuid",
          "description": "L'UUID unique de la tâche à supprimer."
        }
      },
      "required": ["task_id"]
    }
  }
]
```

---

## 💡 Conseils pour le Prompt System de l'Agent IA

Si vous intégrez cette API à un LLM (comme GPT-4 ou Gemini), vous pouvez ajouter cette consigne dans son **System Prompt** :

> *"Tu es un Agent IA assistant personnel. Tu as accès à l'API de gestion des tâches de l'utilisateur. Pour piloter sa liste, tu dois faire des appels REST sur l'API en utilisant l'en-tête `X-API-Key: ai-agent-token-secure-101`. Découvre les spécifications exactes de l'API en interrogeant `/openapi.json`. Assure-toi de respecter les statuts valides : 'A faire', 'En cours', 'Termine'."*
