# Práctica 03: Manipulación de Datos en Conexiones Remotas a Bases de Datos Relacionales

## 📝 Descripción de la Práctica
Esta práctica se enfoca en la administración, importación y manipulación avanzada de datos dentro de un entorno de bases de datos relacionales remoto, aplicado a un contexto de **E-Commerce**. Durante su desarrollo, se exploró la creación de rutinas automatizadas y la inyección masiva de registros para pruebas de estrés y validación de estructura.

## 🛠️ ¿Qué se realizó?
Durante el desarrollo de esta práctica se llevaron a cabo las siguientes acciones principales:

1. **Importación y Restauración de Datos**: 
   - Se analizó y restauró un respaldo parcial (`respaldo05.sql`) de la base de datos `db_test_7b`.
   - Se aislaron e insertaron exitosamente 17 usuarios reales con sus respectivas credenciales encriptadas en la tabla `tb_users`.

2. **Creación de Procedimientos Almacenados (Stored Procedures)**:
   - Se diseñó y ejecutó el procedimiento `GenerarUsuarios()` utilizando bucles (`WHILE`) para automatizar la inserción de **7,500 usuarios** de prueba (dummy data).
   - Se adaptó la estructura de inserción para respetar la arquitectura actual de la tabla (omitiendo columnas obsoletas como `roles` directamente en la tabla y ajustando las longitudes de campos).

3. **Monitoreo y Manejo de Logs**:
   - Se observó el comportamiento de la base de datos ante la inserción masiva, lo que resultó en un crecimiento exponencial de la tabla de auditoría (`tb_logs`), superando los **32,550 registros**, demostrando el registro de eventos transaccionales.

### Tablas de Prácticas de la Materia
| No. | Nombre | Descripción | Potenciador | Estatus |
|---|---|---|---|---|
| 1. | Metodología de Evaluación de la Materia | Transcribir en libreta y comprender la metodología y fechas de Evaluación de la asignatura | 5 | 🟢 Concluida |
| 2. | Conexiones Remotas para Bases de Datos SQL | Crear y administrar usuarios y privilegios de orígenes remotos a través de internet o una red local | 60 | 🟢 Concluida |
| 3 | Manipulación de Datos en Conexiones Remotas a Bases de Datos Relacionales | Crear procedimientos almacenados, funciones, tablas derivadas e importación de datos en el contexto de E-Commerce. ([Diccionario de Datos](https://jhon-1s.github.io/EER-y-Diccionario-de-datos/) \| [Diagrama ER](https://jhon-1s.github.io/EER-y-Diccionario-de-datos/)) | ?? | 🟢 Concluida |
| 4 | Examen Práctico: Instalación de PostgreSQL y MySQL en un VPS | Instalar, configurar, desplegar y simular datos en los servicios de bases de datos relacionales remotas.| ?? | 🟡 En progreso |