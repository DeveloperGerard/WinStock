# WinStock
WinStock es un sistema web con tecnología PWA para la gestión 
de inventarios de alimentos para ganado
e insumos de maquinaria del Fundo San Carlos.


## Django version 6.1.2

para que todos tenga la misma version de Django, instalen los requerimientos 

``` sh
pip install -r requirements.txt
```

### Base de datos
1. Deben de tener instalado PostgreSql -> https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
![alt text](doc/image.png)

2. Al instalar PostgreSql este ya incluye su plataforma propia para administrar bases de datos PostgresSql "pgAdmin 4"

3. Entrar a pgAdmin4 (con la contraseña que creaste durante la instalacion de PostgresSql)
    - Expandir servers
    - Ingresar contraseña
    - Dirigirse a login + (click derecho) + (crear)

4. Configurar usuario
    - General(nombre): winStock_user
    - Definition(contraseña): winStock_user
    - Privilegios(login):true , superuser:true 

5. Configurar base de datos 
    - Click derecho + create
    - General (base de datos): winStock_db
    - Asignar usuario creado
    - Definicion (comprobar que esta en utf8)

6. Crear un archivo .env y configurarlo
    

7. Deben de crear la base de datos mediante las migraciones de Django
    ``` sh
    python manage.py makemigrations

    python manage.py migrate
    ```

con esto se deberian crear todas las tablas en su DBMS
