from pathlib import Path
import os
import environ
from dotenv import load_dotenv


def _split_list(var, default=""):
    return [x.strip() for x in os.getenv(var, default).split(",") if x.strip()]


load_dotenv()
#fijamos la direccion base del archivo a fin de poder referenciar otros archivos
#la palabra reservada para la direccion base es BASE_DIR
#usamos Path(__file__) para obtener la direccion del archivo actual
#luego usamos .resolve() para obtener la ruta absoluta
#y .parent.parent para subir dos niveles en la jerarquia de directorios
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(str(Path(__file__).resolve().parent.parent / ".env"))



#el SECRET_KEY debe ser unico y secreto en produccion
#en desarrollo podemos usar un valor fijo
#usamos esta variable 'SECRET_KEY' para seguridad, permitiendonos firmar cookies y otros datos, a fin de evitar manipulaciones como la falsificacion de solicitudes entre sitios (CSRF)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
#DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
DEBUG = True
# ALLOWED_HOSTS define una lista de nombres de host/domains que esta aplicacion puede servir
# En desarrollo, podemos usar ['*'] para permitir todos los hosts
# En produccion, debemos especificar los nombres de host permitidos
# Un nombre de host hace referencia a la direccion IP o dominio a traves del cual se accede a la aplicacion
ALLOWED_HOSTS = ['*']
#


# --- Proxy detrás de Nginx Proxy Manager ---
USE_X_FORWARDED_HOST = os.getenv("DJANGO_USE_X_FORWARDED_HOST", "False").lower() == "true"
_sp = os.getenv("DJANGO_SECURE_PROXY_SSL_HEADER", "").split(",")
SECURE_PROXY_SSL_HEADER = tuple(_sp) if len(_sp) == 2 else None
SECURE_SSL_REDIRECT = False  # TLS termina en NPM

# --- Hosts permitidos por entorno ---
# Ejemplo de .env: DJANGO_ALLOWED_HOSTS=asistencias.misitiowebpersonal.com.ar,web,localhost,127.0.0.1
ALLOWED_HOSTS = _split_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# --- CSRF por dominio HTTPS (NPM) ---
# Ejemplo de .env: CSRF_TRUSTED_ORIGINS=https://asistencias.misitiowebpersonal.com.ar
_csrf = _split_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = _csrf 


INSTALLED_APPS = [
    'asistencias',
    'django.contrib.admin',#interfaz de administracion
    'django.contrib.auth', #sistema de autenticacion
    'django.contrib.contenttypes',#se usa para establecer relaciones “polimórfica” simple a múltiples modelos. no hace falta especificar a que apunta, como si es necesario en la fk
    'django.contrib.sessions',#gestion de sesiones, ej: mantener a los usuarios autenticados
    'django.contrib.messages',#sistema de mensajeria, ej: mostrar mensajes de exito o error a los usuarios
    'django.contrib.staticfiles',#gestion de archivos estaticos (css, js, imagenes), ej: servir archivos estaticos en desarrollo, sabe donde ir a buscarlos
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    "whitenoise.runserver_nostatic",
    
]

MIDDLEWARE = [ #los middlewares son componentes que procesan las solicitudes y respuestas en la aplicacion, las procesan para agregar funcionalidades como seguridad, gestion de sesiones, etc.
    'django.middleware.security.SecurityMiddleware',#aplica protocolos de seguridad como HTTPS
    'django.contrib.sessions.middleware.SessionMiddleware',#gestiona las sesiones de los usuarios, se materializa mediante cookies, una cookie de sesion identifica a un usuario
    'django.middleware.common.CommonMiddleware',#aplica varias mejoras a las solicitudes y respuestas, como la gestion de redireccionamientos. un ejemplo es redirigir automaticamente las solicitudes sin barra final a la version con barra final
    'django.middleware.csrf.CsrfViewMiddleware',#protege contra ataques de falsificacion de solicitudes entre sitios (CSRF)
    'django.contrib.auth.middleware.AuthenticationMiddleware', #asocia a los usuarios autenticados con las solicitudes
    'django.contrib.messages.middleware.MessageMiddleware',#gestiona los mensajes de un solo uso, como los mensajes de exito o error
    'django.middleware.clickjacking.XFrameOptionsMiddleware',#protege contra ataques de clickjacking
    #los ataques de clickjacking son un tipo de ataque donde un usuario es engañado para hacer clic en algo diferente a lo que el usuario percibe, potencialmente revelando informacion confidencial o permitiendo el control de su computadora mientras interactua con una aplicacion web aparentemente inofensiva
    "allauth.account.middleware.AccountMiddleware",
    'asistencias.middleware.RoleSwitchMiddleware',
    #deploy:
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # antes de CommonMiddleware
    
]

#definimos a donde tiene que ir a buscar los redireccionamientos en el proyecto
ROOT_URLCONF = 'diplomaturas.urls'

#se definen los atributos propios de los templates

TEMPLATES = [
    {
        #backend especifica el motor de plantillas a usar. el motor se encargar de procesar las plantillas y generar el html final.
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        #en dir fijamos donde ir a buscar las templates, de esta direccion se alimenta por ejemplo 'render'
        'DIRS': [BASE_DIR / 'templates'],
        #APP_DIRS=True le dice a django que busque templates dentro de cada app instalada, en una carpeta llamada 'templates'
        'APP_DIRS': True,
        #en optins vamos a encontrar procesadores, que son funciones que nos permiten enviar informacion a las planillas cuando las personalizamos o renderizamos, asi como tambien agregar funcionalidades adicionales al sistema de plantillas, ejemplo el procesador de autenticacion agrega a las plantillas informacion sobre el usuario autenticado
        'OPTIONS': {
            'context_processors': [
                #.debug se usa para mostrar informacion de depuracion en las plantillas cuando DEBUG=True
                'django.template.context_processors.debug',
                #.request agrega el objeto request a las plantillas, permitiendo acceder a informacion sobre la solicitud actual
                'django.template.context_processors.request',
                #.auth agrega informacion sobre el usuario autenticado y sus permisos
                'django.contrib.auth.context_processors.auth',
                #.messages agrega el sistema de mensajeria a las plantillas, permitiendo mostrar mensajes de exito o error a los usuarios
                'django.contrib.messages.context_processors.messages',
                #como estos hay otros procesadores de contextos, cada uno permite agregar funciones o variables.
            ],
        },
    },
]

#definimos el archivo wsgi, que es el punto de entrada para los servidores web compatibles con wsgi. El servidor web usa este archivo para comunicarse con la aplicacion django.
#un servidor compatible seria un servidor como gunicorn o uWSGI, tecnologias que permiten desplegar aplicaciones web escritas en python
WSGI_APPLICATION = 'diplomaturas.wsgi.application'

# Base de datos
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

#se establecen las validaciones de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    #.userattributesimilarityvalidator verifica que la contrasena no sea similar a los atributos del usuario, como su nombre o correo electronico
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    #.minimumlengthvalidator verifica que la contrasena tenga una longitud minima, dicha longitud por defecto son 8 caracteres
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    #.commonpasswordvalidator verifica que la contrasena no sea una contrasena comunmente usada, como "123456" o "password"
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    #.numericpasswordvalidator verifica que la contrasena no sea completamente numerica
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

#language_code establece el lenguaje
LANGUAGE_CODE = 'es-ar'
#la zona horaria. esto puede afectar registros si no esta bien configurada
TIME_ZONE = 'America/Argentina/Buenos_Aires'
#use_l10n habilita la localizacion, que adapta formatos de fechas, numeros y otros datos segun la configuracion regional
USE_I18N = True
#use_tz habilita el soporte de zonas horarias, permitiendo que django maneje fechas y horas de manera consciente de las zonas horarias
USE_TZ = True


#staticfiles_dirs define donde va a ir a buscar a los archivos estaticos, como ser css, imagenes, js, etc
STATICFILES_DIRS = [BASE_DIR / 'static']

#establece como configuracion global, esto se puede cambiar en cada app en app.py, los campos autocompletados, en este caso por un bigautofield que quiere decir un entero grande 
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'asistencias.User'
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

#setea donde se direcciona el login, logout y redireccionamientos
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/'

LOGIN_REDIRECT_URL = 'asistencias:home'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'   # fuerza confirmación por email
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
# Nuevo:
ACCOUNT_LOGIN_METHODS = {"email"}  # o {"email", "username"} si admitís ambos
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]  # podés extender esto luego

ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None 

ACCOUNT_FORMS = {"signup": "asistencias.forms.SignupForm"}

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = int(env('EMAIL_PORT', default=0) or 0)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='no-reply@example.com')


ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

# Static & Media
STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"  # donde collectstatic deja todo
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / "media"
