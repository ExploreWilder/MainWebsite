LOCK TABLES `members` WRITE;
INSERT INTO `members` VALUES (1,'test-admin','pbkdf2:sha512:50000$vt44Zv1A$f29d12ce28ce34ce0e79e20913e73b4624d701064d5a31643c8c91a41a2320068c2390058d63dc6945d8f0fe6f8fb46b7cb680ea3f6a3ae3023d1cd332f9f750',NULL,'root@test.com','',255, '2020-05-30 20:13:53', NULL);
INSERT INTO `members` VALUES (2,'test-user','pbkdf2:sha512:50000$UQubeqDE$0aecc4e0becd16458b94e980b0f855fc82191488cc6cf47899fb315ab7874b982e5eef79fac76777b1215a4a38192c2eb0cec8a6523d274417dbae2630f7026b',NULL,'user@test.com','',190, '2020-05-30 20:13:53', NULL);
INSERT INTO `members` VALUES (3, '','',NULL,'news@letter.com', 'hTeMHrmJTHm0mLLgUiQzZAxiipk79biElYXn3JeO3uiLH0nRvqg8U4lG1t2O5AJW', 0, '2020-05-30 20:13:53', NULL);
UNLOCK TABLES;

LOCK TABLES `gallery` WRITE;
INSERT INTO `gallery` VALUES (1,'test_5u22qzpqo0ivrvvuje8y.jpg','test_neqd7j3vroy5g146rrdyddkli.jpg',511,768,'test_pdv4yzlag46li6pxb2qp1748j8towm.jpg',958,1440,'test_c337e4a059c5b6d4e6cce89f9ffd3acdd4247281.tif',4012,6028,'First photo description.','','2010-05-24 08:01:21','2011-01-26 15:07:10',0,134,'2001-12-28 17:09:10',27,'1/80',8.0,160);
INSERT INTO `gallery` VALUES (2,'test_1vehwefpi6ocpdb7l3qp.jpg','test_nxnqsshy9llai38kxpixysu6x.jpg',1154,768,'test_gvikrlazhkyo6b4fzbsaap6uqwz0ts.jpg',2164,1440,'test_b3b70ae75d13b9b0f99eaf05ab9d7f4ed6a509ce.tif',6028,4012,'','','2011-05-24 08:04:05','2012-01-26 15:07:25',0,136,'2002-12-29 07:18:06',52,'1/80',6.3,100);
INSERT INTO `gallery` VALUES (3,'test_74gdf8hpw41i4qbpnl7b.jpg','test_wkd6xdrmbt9io96zcygpg12gt.jpg',511,768,'test_d607ydjssvuypcbkgo8ws40gf5ykdj.jpg',958,1440,'test_6b253b2e8cc4d46ff1be0f3582e00da29fd481d5.tif',4012,6028,'An other photo description.','','2012-05-24 08:04:39','2015-07-26 15:07:17',1,135,'2015-12-29 07:52:06',27,'1/1',16.0,100);
INSERT INTO `gallery` VALUES (4,'test_9tdkmf8pmpypvq90swxt.jpg','test_byud0m8z8c4oj359785u7mvjd.jpg',1154,768,'test_1zy071k164o6rjjjynvms47kr16a9h.jpg',2164,1440,'test_b4f6add9a5657725d156a94cde808ce8a5d4cf38.tif',6028,4012,'I love me.','','2013-05-24 08:05:33','2019-01-26 15:07:40',240,138,'2015-12-31 18:47:45',450,'1/200',5.6,1000);
INSERT INTO `gallery` VALUES (5,'test_i25b5kne40cudwvh8j0d.jpg','test_ew6wc6fh15h1fef6q5jbkdn4a.jpg',1154,768,'test_3mrhr414l7vtqr4fzydrub782xuqaz.jpg',2164,1440,'test_ce84de696249df6f280814c0132186bb5c0b94ef.tif',6028,4012,'Hello world!','','2014-05-24 08:05:57','2020-01-26 15:07:34',0,137,'2016-12-31 19:13:11',450,'1/250',10.0,100);
UNLOCK TABLES;

LOCK TABLES `shelf` WRITE;
INSERT INTO `shelf` VALUES (1,'first_story','first_story.md','First Title','2018-20','First description.','<p>First description.</p>','2010-08-26 12:28:27','2020-02-07 15:20:17',0,'released',4,NULL,'');
INSERT INTO `shelf` VALUES (2,'second_story','second_story.md','Second Title','1982','Second description.','<p>Second description.</p>','2020-04-26 12:28:27','2020-07-07 15:20:17',0,'released',5,NULL,'');
INSERT INTO `shelf` VALUES (3,'third_story','third_story.md','Third Title','Summer 2014','Third description.','<p>Third description.</p>','2020-04-26 12:28:27','2020-08-07 15:20:17',0,'released',2,NULL,'');
INSERT INTO `shelf` VALUES (4,'fourth_story','fourth_story.md','Fourth Title','','Fourth description.','<p>Fourth description.</p>','2020-01-26 12:28:27','2020-02-07 15:20:17',1,'released',3,NULL,'');
INSERT INTO `shelf` VALUES (5,'fifth_story','fifth_story.md','Random Title','Winter 2019-20','Fifth description.','<p>Fifth description.</p>','2020-02-02 12:28:27','2020-02-07 15:20:17',1,'released',1,NULL,'');
UNLOCK TABLES;
