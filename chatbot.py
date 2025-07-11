#pip install openai chainlit
# Sugerencia para instalar los paquetes necesarios antes de ejecutar el script.

import openai
# Importa el SDK de OpenAI para interactuar con los modelos de lenguaje.

import chainlit as cl
# Importa Chainlit, una librería para crear interfaces conversacionales y manejar mensajes.

import os
# Importa el módulo OS para acceder a variables de entorno del sistema.

# Set Azure OpenAI credentials
# Configura las credenciales necesarias para conectarse a Azure OpenAI.

openai.api_type = "azure"
# Indica que se usará la API de Azure OpenAI.

openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")  # e.g. https://your-resource-name.openai.azure.com/
# Obtiene la URL base del endpoint de Azure OpenAI desde una variable de entorno.

openai.api_key = os.getenv("AZURE_OPENAI_KEY")
# Obtiene la clave de acceso a la API desde una variable de entorno.

openai.api_version = "2023-05-15"  # or the latest supported version
# Especifica la versión de la API de Azure OpenAI que se va a utilizar.

# Model deployment name from Azure (not model name)
# Nombre del despliegue del modelo en Azure, no el nombre del modelo.

DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")  # e.g. "gpt-35-turbo"
# Obtiene el nombre del despliegue del modelo desde una variable de entorno.

@cl.on_message
# Decorador de Chainlit que indica que la función siguiente se ejecuta cuando se recibe un mensaje.

async def main(message: cl.Message):
    # Define una función asíncrona que maneja los mensajes recibidos.

    response = openai.ChatCompletion.create(
        engine=DEPLOYMENT_NAME,
        # Especifica el despliegue del modelo a usar en Azure.

        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            # Mensaje inicial que define el rol del sistema (instrucción para el modelo).

            {"role": "user", "content": message.content}
            # Mensaje del usuario, tomado del contenido recibido por Chainlit.
        ]
    )
    # Llama a la API de OpenAI para obtener una respuesta del modelo.

    reply = response.choices[0].message["content"]
    # Extrae el contenido de la respuesta generada por el modelo.

    await cl.Message(content=reply).send()
    # Envía la respuesta al usuario a través de Chainlit.