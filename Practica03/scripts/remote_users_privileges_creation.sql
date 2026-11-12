/* ==========================================================================================================================================
   1. CREACIÓN DE LA BASE DE DATOS
   ============================================================================================================================================ */
CREATE DATABASE IF NOT EXISTS db_test_7b;
USE db_test_7b;

/* Configuración global para activar roles al iniciar sesión */
SET GLOBAL activate_all_roles_on_login = ON;

/* ==========================================================================================================================================
   2. CREACIÓN DE ROLES
   ============================================================================================================================================ */
CREATE ROLE IF NOT EXISTS 'superadmin';
CREATE ROLE IF NOT EXISTS 'admin';
CREATE ROLE IF NOT EXISTS 'seller';
CREATE ROLE IF NOT EXISTS 'buyer';
CREATE ROLE IF NOT EXISTS 'guest';
CREATE ROLE IF NOT EXISTS 'support';
CREATE ROLE IF NOT EXISTS 'common';
CREATE ROLE IF NOT EXISTS 'user_not_registered';

/* ==========================================================================================================================================
   3. CREACIÓN DE USUARIOS
   ============================================================================================================================================ */
CREATE USER IF NOT EXISTS 'marco.ramirez'@'%' IDENTIFIED BY 'quwerty123';
CREATE USER IF NOT EXISTS 'jonathan.leal'@'%' IDENTIFIED BY '240603';
CREATE USER IF NOT EXISTS 'josu.oloarte'@'%' IDENTIFIED BY '240234';
CREATE USER IF NOT EXISTS 'jey.lara'@'%' IDENTIFIED BY '240234';
CREATE USER IF NOT EXISTS 'rene.david'@'%' IDENTIFIED BY '240107';
CREATE USER IF NOT EXISTS 'margaret.rogas'@'%' IDENTIFIED BY '240242';
CREATE USER IF NOT EXISTS 'app_web'@'%' IDENTIFIED BY 'web123';
CREATE USER IF NOT EXISTS 'app_mobile'@'%' IDENTIFIED BY 'mobile890';

/* asegurar/actualizar contraseñas */
ALTER USER 'marco.ramirez'@'%' IDENTIFIED BY 'quwerty123';
ALTER USER 'jonathan.leal'@'%' IDENTIFIED BY '240603';
ALTER USER 'josu.oloarte'@'%' IDENTIFIED BY '240234';
ALTER USER 'jey.lara'@'%' IDENTIFIED BY '240234';
ALTER USER 'rene.david'@'%' IDENTIFIED BY '240107';
ALTER USER 'margaret.rogas'@'%' IDENTIFIED BY '240242';
ALTER USER 'app_web'@'%' IDENTIFIED BY 'web123';
ALTER USER 'app_mobile'@'%' IDENTIFIED BY 'mobile890';

/* ==========================================================================================================================================
   4. ASIGNACIÓN DE PRIVILEGIOS A LOS ROLES
   ============================================================================================================================================ */

/* SUPERADMIN */
GRANT ALL PRIVILEGES ON *.* TO 'superadmin' WITH GRANT OPTION;

/* ADMIN */
GRANT ALL PRIVILEGES ON db_test_7b.* TO 'admin';

/* SUPPORT */
GRANT SELECT, INSERT, UPDATE ON db_test_7b.tb_users TO 'support';
GRANT SELECT, INSERT, UPDATE ON db_test_7b.tb_products TO 'support';
GRANT SELECT, INSERT, UPDATE ON db_test_7b.tbd_products_categories TO 'support';

/* SELLER */
GRANT SELECT, INSERT, UPDATE ON db_test_7b.* TO 'seller';

/* USER_NOT_REGISTERED (Para conexiones de aplicaciones) */
GRANT INSERT ON db_test_7b.tb_users TO 'user_not_registered';

/* Execución de procedimientos almacenados para no registrados si existen */
-- GRANT EXECUTE ON PROCEDURE db_test_7b.sp_register_new_user TO 'user_not_registered';

/* ==========================================================================================================================================
   5. ASIGNACIÓN DE PRIVILEGIOS DIRECTOS A USUARIOS
   ============================================================================================================================================ */
GRANT ALL PRIVILEGES ON *.* TO 'jonathan.leal'@'%' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON db_test_7b.* TO 'jonathan.leal'@'%';

GRANT ALL PRIVILEGES ON *.* TO 'marco.ramirez'@'%' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON db_test_7b.* TO 'marco.ramirez'@'%';

/* Permisos CRUD directos */
GRANT SELECT, INSERT, UPDATE, DELETE ON db_test_7b.* TO 'josu.oloarte'@'%';

/* ==========================================================================================================================================
   6. ASIGNACIÓN DE ROLES A USUARIOS
   ============================================================================================================================================ */
GRANT 'superadmin' TO 'jonathan.leal'@'%';
GRANT 'admin' TO 'marco.ramirez'@'%';
GRANT 'seller' TO 'josu.oloarte'@'%';
GRANT 'seller' TO 'jey.lara'@'%';
GRANT 'seller' TO 'rene.david'@'%';
GRANT 'support' TO 'margaret.rogas'@'%';

GRANT 'user_not_registered' TO 'app_web'@'%';
GRANT 'user_not_registered' TO 'app_mobile'@'%';

/* ==========================================================================================================================================
   7. DEFINIR ROLES POR DEFECTO
   ============================================================================================================================================ */
SET DEFAULT ROLE ALL TO 'jonathan.leal'@'%';
SET DEFAULT ROLE ALL TO 'marco.ramirez'@'%';
SET DEFAULT ROLE ALL TO 'josu.oloarte'@'%';
SET DEFAULT ROLE ALL TO 'jey.lara'@'%';
SET DEFAULT ROLE ALL TO 'rene.david'@'%';
SET DEFAULT ROLE ALL TO 'margaret.rogas'@'%';
SET DEFAULT ROLE ALL TO 'app_web'@'%';
SET DEFAULT ROLE ALL TO 'app_mobile'@'%';

/* ==========================================================================================================================================
   8. APLICAR CAMBIOS Y VERIFICACIÓN
   ============================================================================================================================================ */
FLUSH PRIVILEGES;

SELECT "Los usuarios y privilegios han sido creados e integrados correctamente" AS mensaje;