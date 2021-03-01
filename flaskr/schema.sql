DROP TABLE IF EXISTS `gallery`;
CREATE TABLE `gallery` (
  `photo_id` int NOT NULL AUTO_INCREMENT,
  `thumbnail_src` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `photo_m_src` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `photo_m_width` smallint unsigned DEFAULT NULL,
  `photo_m_height` smallint unsigned DEFAULT NULL,
  `photo_l_src` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `photo_l_width` smallint unsigned DEFAULT NULL,
  `photo_l_height` smallint unsigned DEFAULT NULL,
  `raw_src` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `raw_width` smallint unsigned DEFAULT NULL,
  `raw_height` smallint unsigned DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modified` timestamp NULL DEFAULT NULL,
  `access_level` tinyint unsigned NOT NULL DEFAULT '0',
  `position` int NOT NULL,
  `date_taken` timestamp NULL DEFAULT NULL,
  `focal_length_35mm` smallint unsigned DEFAULT NULL,
  `exposure_time` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `f_number` float DEFAULT NULL,
  `iso` smallint unsigned DEFAULT NULL,
  PRIMARY KEY (`photo_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `shelf`;
CREATE TABLE `shelf` (
  `book_id` int NOT NULL AUTO_INCREMENT,
  `url` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `period` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description_md` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `description_html` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modified` timestamp NULL DEFAULT NULL,
  `access_level` tinyint unsigned NOT NULL DEFAULT '0',
  `status` enum('crowdfunding','draft','released') COLLATE utf8mb4_unicode_ci DEFAULT 'draft',
  `position` int(11) NOT NULL,
  `crowdfunding_goal` float DEFAULT NULL,
  `preview_card` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`book_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `members_audit_log`;
CREATE TABLE `members_audit_log` (
  `members_audit_log_id` int NOT NULL AUTO_INCREMENT,
  `member_id` int NOT NULL,
  `event_description` enum('logged_in','password_changed','password_reset','email_changed','app_token_generated','app_token_deleted','app_token_used','2fa_enabled','2fa_disabled') COLLATE utf8mb4_unicode_ci DEFAULT 'logged_in',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ip` varbinary(16) DEFAULT NULL,
  PRIMARY KEY (`members_audit_log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `members`;
CREATE TABLE `members` (
  `member_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `one_time_password` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `newsletter_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `access_level` tinyint unsigned NOT NULL DEFAULT '0',
  `date_added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `future_email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `app_token` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `app_hashed_token` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `app_uuid` binary(16) DEFAULT NULL,
  PRIMARY KEY (`member_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `visits`;
CREATE TABLE `visits` (
  `visit_id` int NOT NULL AUTO_INCREMENT,
  `element_id` int NOT NULL,
  `element_type` enum('gallery','shelf') COLLATE utf8mb4_unicode_ci NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ip` varbinary(16) DEFAULT NULL,
  `visitor_id` int DEFAULT NULL,
  `member_id` int DEFAULT NULL,
  `emotion` enum('love','like','neutral','dislike','hate') COLLATE utf8mb4_unicode_ci DEFAULT 'neutral',
  PRIMARY KEY (`visit_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `webhook`;
CREATE TABLE `webhook` (
  `webhook_id` int NOT NULL AUTO_INCREMENT,
  `message_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `curr_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_timestamp` timestamp NULL DEFAULT NULL,
  `type` enum('Donation') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `from_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` float DEFAULT NULL,
  `url` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varbinary(16) DEFAULT NULL,
  PRIMARY KEY (`webhook_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
