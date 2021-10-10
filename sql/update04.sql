CREATE TABLE IF NOT EXISTS `dmap` (
  `user_id` bigint(20) NOT NULL,
  `zoom` float,
  `lat` float,
  `lon` float,
  `style` varchar(64),
  `move_multiplier` float,
  `marker_multiplier` float,
  `levels` varchar(16),
  `iconset` int(16),
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;