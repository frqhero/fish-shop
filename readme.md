`TELEGRAM_TOKEN`  
`STRAPI_TOKEN`  
redis  
`DATABASE_HOST`  
`DATABASE_PORT`  
`DATABASE_PASSWORD`  

Для того чтобы развернуть проект:
* Развернуть strapi
    * install nodejs
        * `snap install node`
    * install strapi
        * `npx create-strapi-app my-project --quickstart`
    * copy old db if you had one
        * `.tmp/data.db`
    * copy model name folder from `src/api` folder of the old project
    * this command might help you out if you forgot the creds  
        `npx strapi admin:reset-user-password --email=frqhero@gmail.com --password=NewPassword123!`