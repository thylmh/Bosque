-- MySQL dump 10.13  Distrib 8.0.44, for Linux (x86_64)
--
-- Host: 35.199.64.147    Database: bosquebd
-- ------------------------------------------------------
-- Server version	8.4.7-google

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `BContrato`
--

DROP TABLE IF EXISTS `BContrato`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BContrato` (
  `id_contrato` varchar(50) NOT NULL,
  `posicion` varchar(50) DEFAULT NULL,
  `cedula` varchar(20) DEFAULT NULL,
  `familia` varchar(100) DEFAULT NULL,
  `cargo` varchar(150) DEFAULT NULL,
  `rol` varchar(150) DEFAULT NULL,
  `banda` varchar(20) DEFAULT NULL,
  `salario` decimal(15,2) DEFAULT NULL,
  `nivel_riesgo` varchar(10) DEFAULT NULL,
  `atep` decimal(10,5) DEFAULT NULL,
  `direccion` varchar(150) DEFAULT NULL,
  `gerencia` varchar(150) DEFAULT NULL,
  `area` varchar(150) DEFAULT NULL,
  `subarea` varchar(150) DEFAULT NULL,
  `tipo_contrato` varchar(100) DEFAULT NULL,
  `num_contrato` varchar(100) DEFAULT NULL,
  `fecha_contrato` date DEFAULT NULL,
  `num_otrosi` varchar(50) DEFAULT NULL,
  `prorrogas_fecha` varchar(50) DEFAULT NULL,
  `fecha_ingreso` date DEFAULT NULL,
  `fecha_terminacion` date DEFAULT NULL,
  `modalidad` varchar(100) DEFAULT NULL,
  `total_dias_tele` decimal(5,1) DEFAULT NULL,
  `sede` varchar(100) DEFAULT NULL,
  `ciudad_contratacion` varchar(150) DEFAULT NULL,
  `estado` varchar(50) DEFAULT NULL,
  `metodo_selec` varchar(100) DEFAULT NULL,
  `encargo` varchar(10) DEFAULT NULL,
  `motivo_ingreso` varchar(150) DEFAULT NULL,
  `fecha_terminacion_real` date DEFAULT NULL,
  `causal_retiro` varchar(255) DEFAULT NULL,
  `usuario` varchar(100) DEFAULT NULL,
  `modificacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id_contrato`),
  KEY `cedula` (`cedula`),
  CONSTRAINT `BContrato_ibfk_1` FOREIGN KEY (`cedula`) REFERENCES `BData` (`cedula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `BData`
--

DROP TABLE IF EXISTS `BData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BData` (
  `cedula` varchar(20) NOT NULL,
  `p_apellido` varchar(100) DEFAULT NULL,
  `s_apellido` varchar(100) DEFAULT NULL,
  `p_nombre` varchar(100) DEFAULT NULL,
  `s_nombre` varchar(100) DEFAULT NULL,
  `correo_electronico` varchar(150) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `genero` varchar(20) DEFAULT NULL,
  `estado_civil` varchar(50) DEFAULT NULL,
  `tipo_sangre` varchar(10) DEFAULT NULL,
  `gestacion` varchar(10) DEFAULT NULL,
  `direccion_residencia` varchar(255) DEFAULT NULL,
  `barrio` varchar(100) DEFAULT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `usuario` varchar(100) DEFAULT NULL,
  `modificacion` datetime DEFAULT NULL,
  PRIMARY KEY (`cedula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `BFinanciacion`
--

DROP TABLE IF EXISTS `BFinanciacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BFinanciacion` (
  `id_financiacion` varchar(50) NOT NULL,
  `id_contrato` varchar(50) DEFAULT NULL,
  `posicion` varchar(50) DEFAULT NULL,
  `cedula` varchar(20) DEFAULT NULL,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_fin` date DEFAULT NULL,
  `salario_base` decimal(15,2) DEFAULT NULL,
  `salario_t` decimal(15,2) DEFAULT NULL,
  `pago_proyectado` decimal(15,2) DEFAULT NULL,
  `rubro` varchar(100) DEFAULT NULL,
  `id_proyecto` varchar(50) DEFAULT NULL,
  `id_fuente` varchar(50) DEFAULT NULL,
  `id_componente` varchar(50) DEFAULT NULL,
  `id_subcomponente` varchar(50) DEFAULT NULL,
  `id_categoria` varchar(50) DEFAULT NULL,
  `id_responsable` varchar(50) DEFAULT NULL,
  `modifico` varchar(100) DEFAULT NULL,
  `modifico_app` varchar(150) DEFAULT NULL,
  `fecha_modificacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id_financiacion`),
  KEY `cedula` (`cedula`),
  KEY `id_contrato` (`id_contrato`),
  CONSTRAINT `BFinanciacion_ibfk_1` FOREIGN KEY (`cedula`) REFERENCES `BData` (`cedula`),
  CONSTRAINT `BFinanciacion_ibfk_2` FOREIGN KEY (`id_contrato`) REFERENCES `BContrato` (`id_contrato`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `BIncremento`
--

DROP TABLE IF EXISTS `BIncremento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BIncremento` (
  `id` varchar(10) NOT NULL,
  `anio` int NOT NULL,
  `smlv` decimal(15,2) NOT NULL,
  `transporte` decimal(15,2) NOT NULL,
  `dotacion` decimal(15,2) NOT NULL,
  `porcentaje_aumento` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `anio` (`anio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_categorias`
--

DROP TABLE IF EXISTS `dim_categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_categorias` (
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_componentes`
--

DROP TABLE IF EXISTS `dim_componentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_componentes` (
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_fuentes`
--

DROP TABLE IF EXISTS `dim_fuentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_fuentes` (
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_proyectos`
--

DROP TABLE IF EXISTS `dim_proyectos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_proyectos` (
  `codigo` text,
  `nombre` text,
  `estado` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_proyectos_otros`
--

DROP TABLE IF EXISTS `dim_proyectos_otros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_proyectos_otros` (
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(255) DEFAULT NULL,
  `estado` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_responsables`
--

DROP TABLE IF EXISTS `dim_responsables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_responsables` (
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_subcomponentes`
--

DROP TABLE IF EXISTS `dim_subcomponentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_subcomponentes` (
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `vista_proyectos_total`
--

DROP TABLE IF EXISTS `vista_proyectos_total`;
/*!50001 DROP VIEW IF EXISTS `vista_proyectos_total`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vista_proyectos_total` AS SELECT 
 1 AS `codigo`,
 1 AS `nombre`,
 1 AS `estado`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping events for database 'bosquebd'
--

--
-- Dumping routines for database 'bosquebd'
--

--
-- Final view structure for view `vista_proyectos_total`
--

/*!50001 DROP VIEW IF EXISTS `vista_proyectos_total`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`bosquebd`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_proyectos_total` AS select `union_proyectos`.`codigo` AS `codigo`,`union_proyectos`.`nombre` AS `nombre`,`union_proyectos`.`estado` AS `estado` from (select `dim_proyectos`.`codigo` AS `codigo`,`dim_proyectos`.`nombre` AS `nombre`,`dim_proyectos`.`estado` AS `estado` from `dim_proyectos` union select `dim_proyectos_otros`.`codigo` AS `codigo`,`dim_proyectos_otros`.`nombre` AS `nombre`,`dim_proyectos_otros`.`estado` AS `estado` from `dim_proyectos_otros` where `dim_proyectos_otros`.`codigo` in (select `dim_proyectos`.`codigo` from `dim_proyectos`) is false) `union_proyectos` order by `union_proyectos`.`nombre` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-22 17:20:00
