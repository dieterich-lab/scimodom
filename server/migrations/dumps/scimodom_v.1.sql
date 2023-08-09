-- MariaDB dump 10.19  Distrib 10.5.19-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: scimodom
-- ------------------------------------------------------
-- Server version	10.5.19-MariaDB-0+deb11u2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `assembly`
--

DROP TABLE IF EXISTS `assembly`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assembly` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `taxa_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `taxa_id` (`taxa_id`),
  CONSTRAINT `assembly_ibfk_1` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assembly`
--

LOCK TABLES `assembly` WRITE;
/*!40000 ALTER TABLE `assembly` DISABLE KEYS */;
INSERT INTO `assembly` VALUES (1,'GRCh38',9606),(2,'GRCm38',10090);
/*!40000 ALTER TABLE `assembly` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `association`
--

DROP TABLE IF EXISTS `association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `association` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  `selection_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dataset_id` (`dataset_id`,`selection_id`),
  KEY `selection_id` (`selection_id`),
  CONSTRAINT `association_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`),
  CONSTRAINT `association_ibfk_2` FOREIGN KEY (`selection_id`) REFERENCES `selection` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `association`
--

LOCK TABLES `association` WRITE;
/*!40000 ALTER TABLE `association` DISABLE KEYS */;
/*!40000 ALTER TABLE `association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `data`
--

DROP TABLE IF EXISTS `data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  `chrom` varchar(128) NOT NULL,
  `start` int(11) NOT NULL,
  `end` int(11) NOT NULL,
  `name` varchar(32) NOT NULL,
  `score` int(11) NOT NULL,
  `strand` varchar(1) NOT NULL,
  `thick_start` int(11) NOT NULL,
  `thick_end` int(11) NOT NULL,
  `item_rgb` varchar(128) NOT NULL,
  `coverage` int(11) NOT NULL,
  `frequency` int(11) NOT NULL,
  `ref_base` varchar(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dataset_id` (`dataset_id`),
  CONSTRAINT `data_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `data`
--

LOCK TABLES `data` WRITE;
/*!40000 ALTER TABLE `data` DISABLE KEYS */;
/*!40000 ALTER TABLE `data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dataset`
--

DROP TABLE IF EXISTS `dataset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dataset` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `project_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `file_format` varchar(32) NOT NULL,
  `modification_type` varchar(32) NOT NULL,
  `taxa_id` int(11) NOT NULL,
  `assembly_id` int(11) NOT NULL,
  `lifted` tinyint(1) NOT NULL,
  `annotation_source` varchar(128) NOT NULL,
  `annotation_version` varchar(128) NOT NULL,
  `sequencing_platform` varchar(255) DEFAULT NULL,
  `basecalling` text DEFAULT NULL,
  `bioinformatics_workflow` text DEFAULT NULL,
  `experiment` text DEFAULT NULL,
  `external_source` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `project_id` (`project_id`),
  KEY `taxa_id` (`taxa_id`),
  KEY `assembly_id` (`assembly_id`),
  CONSTRAINT `dataset_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
  CONSTRAINT `dataset_ibfk_2` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`),
  CONSTRAINT `dataset_ibfk_3` FOREIGN KEY (`assembly_id`) REFERENCES `assembly` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataset`
--

LOCK TABLES `dataset` WRITE;
/*!40000 ALTER TABLE `dataset` DISABLE KEYS */;
/*!40000 ALTER TABLE `dataset` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `method`
--

DROP TABLE IF EXISTS `method`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `method` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cls` varchar(32) NOT NULL,
  `meth` varchar(128) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `method`
--

LOCK TABLES `method` WRITE;
/*!40000 ALTER TABLE `method` DISABLE KEYS */;
/*!40000 ALTER TABLE `method` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `modification`
--

DROP TABLE IF EXISTS `modification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `modification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `rna` varchar(32) NOT NULL,
  `modomics_id` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `modomics_id` (`modomics_id`),
  CONSTRAINT `modification_ibfk_1` FOREIGN KEY (`modomics_id`) REFERENCES `modomics` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `modification`
--

LOCK TABLES `modification` WRITE;
/*!40000 ALTER TABLE `modification` DISABLE KEYS */;
/*!40000 ALTER TABLE `modification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `modomics`
--

DROP TABLE IF EXISTS `modomics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `modomics` (
  `id` varchar(128) NOT NULL,
  `name` varchar(255) NOT NULL,
  `short_name` varchar(32) NOT NULL,
  `moiety` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `modomics`
--

LOCK TABLES `modomics` WRITE;
/*!40000 ALTER TABLE `modomics` DISABLE KEYS */;
INSERT INTO `modomics` VALUES ('00551A','2\'-O-[(5\'-phospho)ribosyl]adenosine-5\'-monophosphate','pAr(p)','nucleotide'),('00551G','2\'-O-ribosylguanosine (phosphate)-5\'-monophosphate','pGr(p)','nucleotide'),('00A','2\'-O-ribosyladenosine (phosphate)','Ar(p)','nucleoside'),('00G','2\'-O-ribosylguanosine (phosphate)','Gr(p)','nucleoside'),('01551A','1,2\'-O-dimethyladenosine-5\'-monophosphate','pm1Am','nucleotide'),('01551G','1,2\'-O-dimethylguanosine-5\'-monophosphate','pm1Gm','nucleotide'),('019551A','1,2\'-O-dimethylinosine-5\'-monophosphate','pm1Im','nucleotide'),('019A','1,2\'-O-dimethylinosine','m1Im','nucleoside'),('01A','1,2\'-O-dimethyladenosine','m1Am','nucleoside'),('01G','1,2\'-O-dimethylguanosine','m1Gm','nucleoside'),('022551G','N2,N2,2\'-O-trimethylguanosine-5\'-monophospate','pm2,2Gm','nucleotide'),('022G','N2,N2,2\'-O-trimethylguanosine','m2,2Gm','nucleoside'),('02551G','N2,2\'-O-dimethylguanosine-5\'-monophospate','pm2Gm','nucleotide'),('02551U','2-thio-2\'-O-methyluridine-5\'-monophosphate','ps2Um','nucleotide'),('027551G','N2,7,2\'-O-trimethylguanosine-5\'-monophosphate','pm2,7Gm','nucleotide'),('027G','N2,7,2\'-O-trimethylguanosine','m2,7Gm','nucleoside'),('02G','N2,2\'-O-dimethylguanosine','m2Gm','nucleoside'),('02U','2-thio-2\'-O-methyluridine','s2Um','nucleoside'),('03551U','3,2\'-O-dimethyluridine-5\'-monophosphate','pm3Um','nucleotide'),('03U','3,2\'-O-dimethyluridine','m3Um','nucleoside'),('042551C','[(2~{R},3~{R},4~{R},5~{R})-5-(4-acetamido-2-oxidanylidene-pyrimidin-1-yl)-4-methoxy-3-oxidanyl-oxolan-2-yl]methyl dihydrogen phosphate','pac4Cm','nucleotide'),('042C','N4-acetyl-2\'-O-methylcytidine','ac4Cm','nucleoside'),('044551C','N4,N4,2\'-O-trimethylcytidine-5\'-monophospate','pm4,4Cm','nucleotide'),('044C','N4,N4,2\'-O-trimethylcytidine','m4,4Cm','nucleoside'),('04551C','4N,O2\'-methylcytidine-5\'-monophosphate','pm4Cm','nucleotide'),('04C','N4,2\'-O-dimethylcytidine','m4Cm','nucleoside'),('0503551U','2\'-O-methyluridine 5-oxyacetic acid methyl ester-5\'-monophosphate','pmcmo5Um','nucleotide'),('0503U','2\'-O-methyluridine 5-oxyacetic acid methyl ester','mcmo5Um','nucleoside'),('051551C','2\'-O-methyl-5-hydroxymethylcytidine-5\'-monophosphate','phm5Cm','nucleotide'),('051551U','5-carboxymethylaminomethyl-2\'-O-methyluridine-5\'-monophosphate','pcmnm5Um','nucleotide'),('051C','2\'-O-methyl-5-hydroxymethylcytidine','hm5Cm','nucleoside'),('051U','5-carboxymethylaminomethyl-2\'-O-methyluridine','cmnm5Um','nucleoside'),('0521551U','5-methoxycarbonylmethyl-2\'-O-methyluridine-5\'-monophosphate','pmcm5Um','nucleotide'),('0521U','5-methoxycarbonylmethyl-2\'-O-methyluridine','mcm5Um','nucleoside'),('0522551U','5-(carboxyhydroxymethyl)-2\'-O-methyluridine methyl ester-5\'-monophosphate','pmchm5Um','nucleotide'),('0522U','5-(carboxyhydroxymethyl)-2\'-O-methyluridine methyl ester','mchm5Um','nucleoside'),('053551U','5-carbamoylmethyl-2\'-O-methyluridine-5\'-monophosphate','pncm5Um','nucleotide'),('053U','5-carbamoylmethyl-2\'-O-methyluridine','ncm5Um','nucleoside'),('0551A','2\'-O-methyladenosine 5\'-(dihydrogen phosphate)','pAm','nucleotide'),('0551C','O2\'-methylcytidine-5\'-monophosphate','pCm','nucleotide'),('0551G','O2\'-methylguanosine-5\'-monophosphate','pGm','nucleotide'),('0551U','O2\'-methyluridine 5\'-monophosphate','pUm','nucleotide'),('05551C','5,2\'-O-dimethylcytidine-5\'-monophosphate','pm5Cm','nucleotide'),('05551U','2\',5-dimethyluridine-5\'-monophosphate','pm5Um','nucleotide'),('0583551U','5-(isopentenylaminomethyl)-2\'-O-methyluridine-5\'-monophosphate','pinm5Um','nucleotide'),('0583U','5-(isopentenylaminomethyl)-2\'-O-methyluridine','inm5Um','nucleoside'),('05C','5,2\'-O-dimethylcytidine','m5Cm','nucleoside'),('05U','5,2\'-O-dimethyluridine','m5Um','nucleoside'),('06551A','N6,2\'-O-dimethyladenosine-5\'-monophospate','pm6Am','nucleotide'),('066551A','N6,N6,2\'-O-trimethyladenosine-5\'-monophospate','pm6,6Am','nucleotide'),('066A','N6,N6,2\'-O-trimethyladenosine','m6,6Am','nucleoside'),('06A','N6,2\'-O-dimethyladenosine','m6Am','nucleoside'),('071551C','5-formyl-2\'-O-methylcytidine-5\'-monophosphate','pf5Cm','nucleotide'),('071C','5-formyl-2\'-O-methylcytidine','f5Cm','nucleoside'),('09551A','2\'-O-methylinosine-5\'-monophosphate','pIm','nucleotide'),('09551U','2\'-O-methylpseudouridine-5\'-monophosphate','pYm','nucleotide'),('09A','2\'-O-methylinosine','Im','nucleoside'),('09U','2\'-O-methylpseudouridine','Ym','nucleoside'),('0A','2\'-O-methyladenosine','Am','nucleoside'),('0C','2\'-O-methylcytidine','Cm','nucleoside'),('0G','2\'-O-methylguanosine','Gm','nucleoside'),('0U','2\'-O-methyluridine','Um','nucleoside'),('0X','unknown nucleoside 2\'-O-methylated','Xm','nucleoside'),('100000G','7-cyano-7-carbaguanine','preQ0base','base'),('10000G','queuine','Qbase','base'),('100551G','7-cyano-7-deazaguanosine-5\'-monophosphate','ppreQ0','nucleotide'),('100G','7-cyano-7-deazaguanosine','preQ0','nucleoside'),('101000G','7-aminomethyl-7-carbaguanine','preQ1base','base'),('101551G','7-aminomethyl-7-deazaguanosine-5\'-monophosphate','ppreQ1','nucleotide'),('101G','7-aminomethyl-7-deazaguanosine','preQ1','nucleoside'),('102551G','epoxyqueuosine-5\'-monophosphate','poQ','nucleotide'),('102G','epoxyqueuosine','oQ','nucleoside'),('103551G','archaeosine-5\'-monophosphate','pG+','nucleotide'),('103G','archaeosine','G+','nucleoside'),('104551G','galactosyl-queuosine-5\'-monophosphate','pgalQ','nucleotide'),('104G','galactosyl-queuosine','galQ','nucleoside'),('10551G','queuosine-5\'-monophospate','pQ','nucleotide'),('105551G','glutamyl-queuosine-5\'-monophosphate','pgluQ','nucleotide'),('105G','glutamyl-queuosine','gluQ','nucleoside'),('106551G','mannosyl-queuosine-5\'-monophosphate','pmanQ','nucleotide'),('106G','mannosyl-queuosine','manQ','nucleoside'),('10G','queuosine','Q','nucleoside'),('1309551U','3-(3-amino-3-carboxypropyl)pseudouridine-5\'-monophosphate','pm1acp3Y','nucleotide'),('1309U','1-methyl-3-(3-amino-3-carboxypropyl)pseudouridine','m1acp3Y','nucleoside'),('1551A','6-hydro-1-methyladenosine-5\'-monophosphate','pm1A','nucleotide'),('1551G','1N-methylguanosine-5\'-monophosphate','pm1G','nucleotide'),('1551N','alpha-methylmonophosphate 5\' cap','mpN','nucleotide'),('1553N','gamma-methyltriphosphate 5\' cap','mpppN','nucleotide'),('19551A','1-methylinosine-5\'-monophosphate','pm1I','nucleotide'),('19551U','1-methylpseudouridine-5\'-monophosphate','pm1Y','nucleotide'),('19A','1-methylinosine','m1I','nucleoside'),('19U','1-methylpseudouridine','m1Y','nucleoside'),('1A','1-methyladenosine','m1A','nucleoside'),('1G','1-methylguanosine','m1G','nucleoside'),('20510551U','5-aminomethyl-2-selenouridine-5\'-monophosphate','pnm5se2U','nucleotide'),('20510U','5-aminomethyl-2-selenouridine','nm5se2U','nucleoside'),('20511551U','5-methylaminomethyl-2-selenouridine-5\'-monophosphate','pmnm5se2U','nucleotide'),('20511U','5-methylaminomethyl-2-selenouridine','mnm5se2U','nucleoside'),('2051551U','5-carboxymethylaminomethyl-2-selenouridine-5\'-monophosphate','pcmnm5se2U','nucleotide'),('2051U','5-carboxymethylaminomethyl-2-selenouridine','cmnm5se2U','nucleoside'),('20551C','agmatidine-5\'-monophosphate','pC+','nucleotide'),('20551U','1-(5-O-phosphono-beta-D-ribofuranosyl)-2-selanylpyrimidin-4(1H)-one','pse2U','nucleotide'),('20C','agmatidine','C+','nucleoside'),('20U','2-selenouridine','se2U','nucleoside'),('21161551A','2- methylthiomethylenethio-N6-isopentenyl-adenosine-5\'-monophosphate','pmsms2i6A','nucleotide'),('21161A','2- methylthiomethylenethio-N6-isopentenyl-adenosine','msms2i6A','nucleoside'),('21510551U','5-aminomethyl-2-geranylthiouridine-5\'-monophosphate','pnm5ges2U','nucleotide'),('21510U','5-aminomethyl-2-geranylthiouridine','nm5ges2U','nucleoside'),('21511551U','5-methylaminomethyl-2-geranylthiouridine-5\'-monophosphate','pmnm5ges2U','nucleotide'),('21511U','5-methylaminomethyl-2-geranylthiouridine','mnm5ges2U','nucleoside'),('2151551U','5-carboxymethylaminomethyl-2-geranylthiouridine-5\'-monophosphate','pcmnm5ges2U','nucleotide'),('2151U','5-carboxymethylaminomethyl-2-geranylthiouridine','cmnm5ges2U','nucleoside'),('21551C','2-lysidine-5\'-monophosphate','pk2C','nucleotide'),('21551U','2-geranylthiouridine-5\'-monophosphate','pges2U','nucleotide'),('2160551A','2-methylthio-N6-(cis-hydroxyisopentenyl) adenosine-5\'-monophosphate','pms2io6A','nucleotide'),('2160A','2-methylthio-N6-(cis-hydroxyisopentenyl) adenosine','ms2io6A','nucleoside'),('2161551A','2-methylthio-N6-isopentenyl-adenosine-5\'-monophosphate','pms2i6A','nucleotide'),('2161A','2-methylthio-N6-isopentenyladenosine','ms2i6A','nucleoside'),('2162551A','2-methylthio-N6-threonylcarbamoyladenosine-5\'-monophosphate','pms2t6A','nucleotide'),('2162A','2-methylthio-N6-threonylcarbamoyladenosine','ms2t6A','nucleoside'),('2163551A','2-methylthio-N6-hydroxynorvalylcarbamoyladenosine-5\'-monophosphate','pms2hn6A','nucleotide'),('2163A','2-methylthio-N6-hydroxynorvalylcarbamoyladenosine','ms2hn6A','nucleoside'),('2164551A','2-methylthio cyclic N6-threonylcarbamoyladenosine-5\'-monophosphate','pms2ct6A','nucleotide'),('2164A','2-methylthio cyclic N6-threonylcarbamoyladenosine','ms2ct6A','nucleoside'),('2165551A','hydroxy-N6-threonylcarbamoyladenosine-5\'-monophosphate','pht6A','nucleotide'),('2165A','hydroxy-N6-threonylcarbamoyladenosine','ht6A','nucleoside'),('21C','2-lysidine','k2C','nucleoside'),('21U','2-geranylthiouridine','ges2U','nucleoside'),('22551G','N2-dimethylguanosine-5\'-monophosphate','pm2,2G','nucleotide'),('227551G','N2,N2,7-trimethylguanosine-5\'-monophosphate','pm2,2,7G','nucleotide'),('2279553N','N2,N2,7-trimethylguanosine cap (cap TMG)','m2,2,7GpppN','nucleotide'),('227G','N2,N2,7-trimethylguanosine','m2,2,7G','nucleoside'),('22G','N2,N2-dimethylguanosine','m2,2G','nucleoside'),('2510551U','5-aminomethyl-2-thiouridine-5\'-monophosphate','pnm5s2U','nucleotide'),('2510U','5-aminomethyl-2-thiouridine','nm5s2U','nucleoside'),('2511551U','5-methylaminomethyl-2-thiouridine-5\'-monophosphate','pmnm5s2U','nucleotide'),('2511U','5-methylaminomethyl-2-thiouridine','mnm5s2U','nucleoside'),('251551U','5-carboxymethylaminomethyl-2-thiouridine-5\'-monophosphate','pcmnm5s2U','nucleotide'),('251U','5-carboxymethylaminomethyl-2-thiouridine','cmnm5s2U','nucleoside'),('2521551U','5-(O-methylaceto)-2-thio-2-deoxy-uridine-5\'-monophosphate','pmcm5s2U','nucleotide'),('2521U','5-methoxycarbonylmethyl-2-thiouridine','mcm5s2U','nucleoside'),('253551U','5-carbamoylmethyl-2-thiouridine-5\'-monophosphate','pncm5s2U','nucleotide'),('253U','5-carbamoylmethyl-2-thiouridine','ncm5s2U','nucleoside'),('2540551U','5-carboxymethyl-2-thiouridine-5\'-monophosphate','pcm5s2U','nucleotide'),('2540U','5-carboxymethyl-2-thiouridine','cm5s2U','nucleoside'),('254551U','5-taurinomethyl-2-thiouridine-5\'-monophosphate','ptm5s2U','nucleotide'),('254U','5-taurinomethyl-2-thiouridine','tm5s2U','nucleoside'),('2551A','2-methyladenosine-5\'-monophosphate','pm2A','nucleotide'),('2551C','2-thiocytidine-5\'-monophosphate','ps2C','nucleotide'),('2551G','2N-methylguanosine-5\'-monophosphate','pm2G','nucleotide'),('2551N','alpha-dimethylmonophosphate 5\' cap','mmpN','nucleotide'),('2551U','1-(beta-D-ribofuranosyl)-2-thio-uracil-5\'-phosphate','ps2U','nucleotide'),('25551U','5-methyl-2-thiouridine-5\'-monophosphate','pm5s2U','nucleotide'),('255N','5\' nicotinamide adenine dinucleotide','NADpN','nucleotide'),('2583551U','5-(isopentenylaminomethyl)-2-thiouridine-5\'-monophosphate','pinm5s2U','nucleotide'),('2583U','5-(isopentenylaminomethyl)-2-thiouridine','inm5s2U','nucleoside'),('25U','5-methyl-2-thiouridine','m5s2U','nucleoside'),('27551G','N2,7-dimethylguanosine-5\'-monophosphate','pm2,7G','nucleotide'),('279553N','N2,7-dimethylguanosine cap (cap DMG)','m2,7GpppN','nucleotide'),('27G','N2,7-dimethylguanosine','m2,7G','nucleoside'),('28551A','2,8-dimethyladenosine-5\'-monophosphate','pm2,8A','nucleotide'),('28A','2,8-dimethyladenosine','m2,8A','nucleoside'),('2A','2-methyladenosine','m2A','nucleoside'),('2C','2-thiocytidine','s2C','nucleoside'),('2G','N2-methylguanosine','m2G','nucleoside'),('2U','2-thiouridine','s2U','nucleoside'),('30551U','3-(3-amino-3-carboxypropyl)uridine-5\'-monophosphate','pacp3U','nucleotide'),('308551U','3-(3-amino-3-carboxypropyl)-5,6-dihydrouridine-5\'-monophosphate','pacp3D','nucleotide'),('308U','3-(3-amino-3-carboxypropyl)-5,6-dihydrouridine','acp3D','nucleoside'),('309U','3-(3-amino-3-carboxypropyl)pseudouridine','acp3Y','nucleoside'),('30U','3-(3-amino-3-carboxypropyl)uridine','acp3U','nucleoside'),('33551A','adenosine-3\',5\'-diphosphate','pAp','nucleotide'),('33551G','guanosine-3\',5\'-diphosphate','pGp','nucleotide'),('3377551U','uridine-5\'-monophosphate-2\',3\'-cyclic phosphate','pU2\'3\'cp','nucleotide'),('3377A','adenosine-5\'-phosphate-2\',3\'-cyclic phosphate','pA2\'3\'cp','nucleotide'),('3377C','cytidine-5\'-phosphate-2\',3\'-cyclic phosphate','pC2\'3\'cp','nucleotide'),('3377G','guanoside-5\'-phosphate-2\',3\'-cyclic phosphate','pG2\'3\'cp','nucleotide'),('3377N','2\'3\'-cyclic phosphate end','N2\'3\'cp','nucleotide'),('342551G','methylwyosine-5\'-monophosphate','pmimG','nucleotide'),('342G','methylwyosine','mimG','nucleoside'),('34551G','wyosine-5\'-monophospate','pimG','nucleotide'),('3470551G','undermodified hydroxywybutosine-5\'-monophospate','pOHyWx','nucleotide'),('3470G','undermodified hydroxywybutosine','OHyWx','nucleoside'),('347551G','7-aminocarboxypropylwyosine-5\'-monophosphate','pyW-72','nucleotide'),('347G','7-aminocarboxypropylwyosine','yW-72','nucleoside'),('3480551G','methylated undermodified hydroxywybutosine-5\'-monophosphate','pOHyWy','nucleotide'),('3480G','methylated undermodified hydroxywybutosine','OHyWy','nucleoside'),('34830551G','hydroxywybutosine-5\'-monophosphate','pOHyW','nucleotide'),('34830G','hydroxywybutosine','OHyW','nucleoside'),('34831551G','wybutosine[C15(S)]-5\'-monophosphate','pyW','nucleotide'),('34832G','peroxywybutosine','o2yW','nucleoside'),('3483551G','wybutosine-5\'-monophosphate','pyW','nucleotide'),('3483G','wybutosine','yW','nucleoside'),('348551G','7-aminocarboxypropylwyosine methyl ester-5\'-monophosphate','pyW-58','nucleotide'),('348G','7-aminocarboxypropylwyosine methyl ester','yW-58','nucleoside'),('34G','wyosine','imG','nucleoside'),('3551C','3-Methylcytidine- 5\'-monophosphate','pm3C','nucleotide'),('3551U','3-methyluridine-5\'-monophosphate','pm3U','nucleotide'),('39551U','3-methylpseudouridine-5\'-monophosphate','pm3Y','nucleotide'),('39U','3-methylpseudouridine','m3Y','nucleoside'),('3C','3-methylcytidine','m3C','nucleoside'),('3U','3-methyluridine','m3U','nucleoside'),('4155N','5\' (3\' -dephosphoacetyl-CoA)','acCoApN','nucleotide'),('42551C','N(4)-acetylcytidine-5\'-monophosphate','pac4C','nucleotide'),('42551G','isowyosine-5\'-monophosphate','pimG2','nucleotide'),('4255N','5\' (3\' -dephosphomalonyl-CoA)','malonyl-CoApN','nucleotide'),('42C','N4-acetylcytidine','ac4C','nucleoside'),('42G','isowyosine','imG2','nucleoside'),('4355N','5\' (3\' -dephosphosuccinyl-CoA)','succinyl-CoApN','nucleotide'),('44551C','[(2~{R},3~{S},4~{R},5~{R})-5-[4-(dimethylamino)-2-oxidanylidene-pyrimidin-1-yl]-3,4-bis(oxidanyl)oxolan-2-yl]methyl dihydrogen phosphate','pm4,4C','nucleotide'),('44C','N4,N4-dimethylcytidine','m4,4C','nucleoside'),('4551C','4-methyl, cytidine-5\'-monophosphate','pm4C','nucleotide'),('4551G','4-demethylwyosine-5\'-monophosphate','pimG-14','nucleotide'),('4553N','adenosine triphosphate 5\' cap (cap A)','ApppN','nucleotide'),('4554N','adenosine tetraphosphate 5\' cap (cap Ap4N)','AppppN','nucleotide'),('4555N','adenosine pentaphosphate 5\' cap (cap Ap5N)','ApppppN','nucleotide'),('455N','5\' (3\' -dephospho-CoA)','CoApN','nucleotide'),('47551G','7-aminocarboxypropyl-demethylwyosine-5\'-monophosphate','pyW-86','nucleotide'),('47G','7-aminocarboxypropyl-demethylwyosine','yW-86','nucleoside'),('4C','N4-methylcytidine','m4C','nucleoside'),('4G','4-demethylwyosine','imG-14','nucleoside'),('501551U','5-methoxyuridine-5\'-monophosphate','pmo5U','nucleotide'),('501U','5-methoxyuridine','mo5U','nucleoside'),('502551U','5-(carboxymethoxy) uridine-5\'-monophosphate','pcmo5U','nucleotide'),('502U','uridine 5-oxyacetic acid','cmo5U','nucleoside'),('503551U','uridine 5-oxyacetic acid methyl ester-5\'-monophospate','pmcmo5U','nucleotide'),('503U','uridine 5-oxyacetic acid methyl ester','mcmo5U','nucleoside'),('50551C','5-hydroxycytidine-5\'-monophosphate','pho5C','nucleotide'),('50551U','5-hydroxyuridine-5\'-monophosphate','pho5U','nucleotide'),('50C','5-hydroxycytidine','ho5C','nucleoside'),('50U','5-hydroxyuridine','ho5U','nucleoside'),('510551U','5-aminomethyluridine-5\'-monophosphate','pnm5U','nucleotide'),('510U','5-aminomethyluridine','nm5U','nucleoside'),('511551U','(2R,4S)-1-[(4R)-3,4-dihydroxytetrahydrofuran-2-YL]-5-[(methylamino)methyl]-1,2,3,4-tetrahydropyrimidine-2,4-diol-5\'-monophosphate','pmnm5U','nucleotide'),('511U','5-methylaminomethyluridine','mnm5U','nucleoside'),('51551C','5-(hydroxymethyl)cytidine 5\'-(dihydrogen phosphate)','phm5C','nucleotide'),('51551U','5-carboxymethylaminomethyluridine-5\'-monophosphate','pcmnm5U','nucleotide'),('51C','5-hydroxymethylcytidine','hm5C','nucleoside'),('51U','5-carboxymethylaminomethyluridine','cmnm5U','nucleoside'),('520551U','5-carboxyhydroxymethyluridine-5\'-monophosphate','pchm5U','nucleotide'),('520U','5-carboxyhydroxymethyluridine','chm5U','nucleoside'),('521551U','5-methoxycarbonylmethyluridine-5\'-monophosphate','pmcm5U','nucleotide'),('521U','5-methoxycarbonylmethyluridine','mcm5U','nucleoside'),('522551U','5-(carboxyhydroxymethyl)uridine methyl ester-5\'-monophosphate','pmchm5U','nucleotide'),('522U','5-(carboxyhydroxymethyl)uridine methyl ester','mchm5U','nucleoside'),('52551U','5-carboxymethyluridine-5\'-monophosphate','pcm5U','nucleotide'),('52U','5-carboxymethyluridine','cm5U','nucleoside'),('531551U','5-carbamoylhydroxymethyluridine-5\'-monophosphate','pnchm5U','nucleotide'),('531U','5-carbamoylhydroxymethyluridine','nchm5U','nucleoside'),('53551U','5-carbamoylmethyluridine-5\'-monophosphate','pncm5U','nucleotide'),('53U','5-carbamoylmethyluridine','ncm5U','nucleoside'),('54551U','5-taurinomethyluridine-5\'-monophosphate','ptm5U','nucleotide'),('54U','5-taurinomethyluridine','tm5U','nucleoside'),('550N','5\' hydroxyl end','5\'-OH-N','nucleoside'),('551A','adenosine-5\'-monophosphate','pA','nucleotide'),('551C','cytidine-5\'-monophosphate','pC','nucleotide'),('551G','guanosine-5\'-monophosphate','pG','nucleotide'),('551G551N','guanosine added to any ribonucleotide','pG(pN)','nucleotide'),('551N','unknown 5\' monophosphate ribonucleotide','pN','nucleotide'),('551U','uridine-5\'-monophosphate','pU','nucleotide'),('552G','guanosine-5\'-diphosphate','ppG','nucleotide'),('552N','5\' diphosphate end','ppN','nucleotide'),('553A','adenosine-5\'-triphosphate','pppA','nucleotide'),('553G','guanosine-5\'-triphosphate','pppG','nucleotide'),('553N','5\' triphosphate end','pppN','nucleotide'),('5551C','5-methylcytidine-5\'-monophosphate','pm5C','nucleotide'),('5551U','5-methyluridine-5\'-monophosphate','pm5U','nucleotide'),('55551U','5-cyanomethyluridine-5\'-monophosphate','pcnm5U','nucleotide'),('55U','5-cyanomethyluridine','cnm5U','nucleoside'),('583551U','5-(isopentenylaminomethyl)uridine-5\'-monophosphate','pinm5U','nucleotide'),('583U','5-(isopentenylaminomethyl)uridine','inm5U','nucleoside'),('58551U','5-methyldihydrouridine-5\'-monophosphate','pm5D','nucleotide'),('58U','5-methyldihydrouridine','m5D','nucleoside'),('5C','5-methylcytidine','m5C','nucleoside'),('5U','5-methyluridine','m5U','nucleoside'),('60551A','N6-(cis-hydroxyisopentenyl)adenosine-5\'-monophospate','pio6A','nucleotide'),('60A','N6-(cis-hydroxyisopentenyl)adenosine','io6A','nucleoside'),('61551A','N6-isopentenyl-adenosine-5\'-monophosphate','pi6A','nucleotide'),('61A','N6-isopentenyladenosine','i6A','nucleoside'),('621551A','2-methylthio-N6-methyladenosine-5\'-monophosphate','pms2m6A','nucleotide'),('621A','2-methylthio-N6-methyladenosine','ms2m6A','nucleoside'),('62551A','N6-threonylcarbamoyladenosine-5\'-monophosphate','pt6A','nucleotide'),('62A','N6-threonylcarbamoyladenosine','t6A','nucleoside'),('63551A','N6-hydroxynorvalylcarbamoyladenosine-5\'-monophosphate','phn6A','nucleotide'),('63A','N6-hydroxynorvalylcarbamoyladenosine','hn6A','nucleoside'),('64551A','N6-acetyladenosine-5\'-monophospate','pac6A','nucleotide'),('64553N','N6-methyl-adenosine triphosphate 5\' cap (cap A)','m6ApppN','nucleotide'),('64554N','N6-methyl-adenosine tetraphosphate 5\' cap (cap Ap4N)','m6AppppN','nucleotide'),('64555N','N6-methyl-adenosine pentaphosphate 5\' cap (cap Ap5N)','m6ApppppN','nucleotide'),('64A','N6-acetyladenosine','ac6A','nucleoside'),('6551A','N6-methyladenosine-5\'-monophosphate','pm6A','nucleotide'),('65551A','N6-glycinylcarbamoyladenosine-5\'-monophosphate','pg6A','nucleotide'),('65A','N6-glycinylcarbamoyladenosine','g6A','nucleoside'),('662551A','N6-methyl-N6-threonylcarbamoyladenosine-5\'-monophosphate','pm6t6A','nucleotide'),('662A','N6-methyl-N6-threonylcarbamoyladenosine','m6t6A','nucleoside'),('66551A','6N-dimethyladenosine-5\'-monophosphate','pm6,6A','nucleotide'),('66A','N6,N6-dimethyladenosine','m6,6A','nucleoside'),('67551A','N6-formyladenosine-5\'-monophospate','pf6A','nucleotide'),('67A','N6-formyladenosine','f6A','nucleoside'),('68551A','N6-hydroxymethyladenosine-5\'-monophosphate','phm6A','nucleotide'),('68A','N6-hydroxymethyladenosine','hm6A','nucleoside'),('69551A','cyclic N6-threonylcarbamoyladenosine-5\'-monophosphate','pct6A','nucleotide'),('69A','cyclic N6-threonylcarbamoyladenosine','ct6A','nucleoside'),('6A','N6-methyladenosine','m6A','nucleoside'),('71551C','5-formylcytidine 5\'-(dihydrogen phosphate)','pf5C','nucleotide'),('71C','5-formylcytidine','f5C','nucleoside'),('74551U','4-thiouridine-5\'-monophosphate','ps4U','nucleotide'),('74U','4-thiouridine','s4U','nucleoside'),('7551G','7N-methyl-8-hydroguanosine-5\'-monophosphate','pm7G','nucleotide'),('79553N','N7-methyl-guanosine cap (cap 0)','m7GpppN','nucleotide'),('79554N','N7-methyl-guanosine  tetraphosphate 5\' cap (cap m7Gp4N)','m7GppppN','nucleotide'),('7G','7-methylguanosine','m7G','nucleoside'),('8551A','8-methyladenosine-5\'-monophosphate','pm8A','nucleotide'),('8551U','5,6-dihydrouridine-5\'-monophosphate','pD','nucleotide'),('8A','8-methyladenosine','m8A','nucleoside'),('8U','dihydrouridine','D','nucleoside'),('9551A','inosine-5\'-monophosphate','pI','nucleotide'),('9551U','pseudouridine-5\'-monophosphate','pY','nucleotide'),('9553N','guanosine triphosphate 5\' cap (cap G)','GpppN','nucleotide'),('9A','inosine','I','nucleoside'),('9U','pseudouridine','Y','nucleoside'),('?A','unknown modified adenosine','xA','nucleoside'),('?C','unknown modified cytidine','xC','nucleoside'),('?G','unknown modified guanosine','xG','nucleoside'),('?U','unknown modified uridine','xU','nucleoside'),('A','adenosine','A','nucleoside'),('C','cytidine','C','nucleoside'),('G','guanosine','G','nucleoside'),('N','unknown ribonucleoside residue','N','nucleoside'),('U','uridine','U','nucleoside'),('X','unknown modification','xX','nucleoside');
/*!40000 ALTER TABLE `modomics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ncbi_taxa`
--

DROP TABLE IF EXISTS `ncbi_taxa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ncbi_taxa` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `taxonomy_id` int(11) NOT NULL,
  `short_name` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `taxonomy_id` (`taxonomy_id`),
  CONSTRAINT `ncbi_taxa_ibfk_1` FOREIGN KEY (`taxonomy_id`) REFERENCES `taxonomy` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10091 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ncbi_taxa`
--

LOCK TABLES `ncbi_taxa` WRITE;
/*!40000 ALTER TABLE `ncbi_taxa` DISABLE KEYS */;
INSERT INTO `ncbi_taxa` VALUES (562,'Escherichia coli',6,'E. coli'),(3702,'Arabidopsis thaliana',5,'A. thaliana'),(4932,'Saccharomyces cerevisiae',4,'S. cerevisiae'),(6239,'Caenorhabditis elegans',3,'C. elegans'),(7227,'Drosophila melanogaster',2,'D. melanogaster'),(9606,'Homo sapiens',1,'H. sapiens'),(10090,'Mus musculus',1,'M. musculus');
/*!40000 ALTER TABLE `ncbi_taxa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `organism`
--

DROP TABLE IF EXISTS `organism`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `organism` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cto` varchar(255) NOT NULL,
  `taxa_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `taxa_id` (`taxa_id`),
  CONSTRAINT `organism_ibfk_1` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `organism`
--

LOCK TABLES `organism` WRITE;
/*!40000 ALTER TABLE `organism` DISABLE KEYS */;
/*!40000 ALTER TABLE `organism` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `summary` text NOT NULL,
  `contact_name` varchar(128) NOT NULL,
  `contact_institution` varchar(255) NOT NULL,
  `contact_email` varchar(320) NOT NULL,
  `date_published` datetime NOT NULL,
  `date_added` datetime NOT NULL,
  `doi` varchar(255) DEFAULT NULL,
  `pmid` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project`
--

LOCK TABLES `project` WRITE;
/*!40000 ALTER TABLE `project` DISABLE KEYS */;
/*!40000 ALTER TABLE `project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `selection`
--

DROP TABLE IF EXISTS `selection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `selection` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `modification_id` int(11) NOT NULL,
  `technology_id` int(11) NOT NULL,
  `organism_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `modification_id` (`modification_id`,`technology_id`,`organism_id`),
  KEY `technology_id` (`technology_id`),
  KEY `organism_id` (`organism_id`),
  CONSTRAINT `selection_ibfk_1` FOREIGN KEY (`modification_id`) REFERENCES `modification` (`id`),
  CONSTRAINT `selection_ibfk_2` FOREIGN KEY (`technology_id`) REFERENCES `technology` (`id`),
  CONSTRAINT `selection_ibfk_3` FOREIGN KEY (`organism_id`) REFERENCES `organism` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `selection`
--

LOCK TABLES `selection` WRITE;
/*!40000 ALTER TABLE `selection` DISABLE KEYS */;
/*!40000 ALTER TABLE `selection` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `taxonomy`
--

DROP TABLE IF EXISTS `taxonomy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taxonomy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(32) NOT NULL,
  `kingdom` varchar(32) DEFAULT NULL,
  `phylum` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taxonomy`
--

LOCK TABLES `taxonomy` WRITE;
/*!40000 ALTER TABLE `taxonomy` DISABLE KEYS */;
INSERT INTO `taxonomy` VALUES (1,'Eukarya','Animalia','Chordata'),(2,'Eukarya','Animalia','Arthropoda'),(3,'Eukarya','Animalia','Nematoda'),(4,'Eukarya','Fungi',NULL),(5,'Eukarya','Plantae',NULL),(6,'Bacteria',NULL,NULL),(7,'Vira',NULL,NULL);
/*!40000 ALTER TABLE `taxonomy` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `technology`
--

DROP TABLE IF EXISTS `technology`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `technology` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tech` varchar(255) NOT NULL,
  `method_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `method_id` (`method_id`),
  CONSTRAINT `technology_ibfk_1` FOREIGN KEY (`method_id`) REFERENCES `method` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `technology`
--

LOCK TABLES `technology` WRITE;
/*!40000 ALTER TABLE `technology` DISABLE KEYS */;
/*!40000 ALTER TABLE `technology` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-08-09 14:20:49
