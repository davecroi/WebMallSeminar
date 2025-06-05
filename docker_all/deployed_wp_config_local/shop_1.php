<?php
/**
 * The base configuration for WordPress
 *
 * @link https://developer.wordpress.org/advanced-administration/wordpress/wp-config/
 * @package WordPress
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'bitnami_wordpress' );

/** Database username */
define( 'DB_USER', 'bn_wordpress' );

/** Database password */
// ****** IMPORTANT: Replace 'wordpress_db_password' with your actual DB password ******
define( 'DB_PASSWORD', 'wordpress_db_password' );

/** Database hostname */
define( 'DB_HOST', 'mariadb_shop1:3306' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 * Change these to different unique phrases!
 * You can generate these using the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}
 *
 * @since 2.6.0
 */
// ****** IMPORTANT: These keys should be unique to your site. ******
// ****** If this is a new site, regenerate them from the link above. ******
define( 'AUTH_KEY',         '. ~R8XIG]?G}e:{mH30n#L{{*g6cXmy:n*-V?!zHrf%(nL8AJ8_k?S,..BFc*%yD' );
define( 'SECURE_AUTH_KEY',  'IvLi3K4T`vm#%[6`A:z6MLpu1$o~$jG5gtZ^!sy(Q{>&Q*F38CA7>Nt`Y*jeNuc|' );
define( 'LOGGED_IN_KEY',    '?1}n} BhU@rO_=#J%?bTq;;>[)EOim}nV=~l[M5em#`<]h*%wCTm9`hbj4dR47o)' );
define( 'NONCE_KEY',        '6lai1^zNnF*V1i8b#!Rvw4UayTwlu)s-~2U]Ko{TT9P5>tv!gzOR,y):U)~C&wO~' );
define( 'AUTH_SALT',        '^c%sX|A[nCeN[g}cUqD7&dv)5o/g+J9C8u!bhUTXR,6AW:)c)JG!Vd 4!(G.!uqG' );
define( 'SECURE_AUTH_SALT', ':LRP[Y~G}>?w`L~*oq/5L0mw:L+_1AH[Ary5j0F+D8<xpgC#^8c25{,4i:iE*@{X' );
define( 'LOGGED_IN_SALT',   'ej/X sJXJ]w{88yd)4q~O4rlUV#(QbL%{A2ac3NSr1HO@pl?PW2EwDU]/34?JmmA' );
define( 'NONCE_SALT',       'l!x{9/|adgf0{wS`Ras_`DAUROx1vWjy3Y{*{ngki3v6t/w9|!1U!S/RwtBFr[K5' );
/**#@-*/

/**
 * WordPress database table prefix.
 */
$table_prefix = 'wp_';

/**
 * For developers: WordPress debugging mode.
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments. For production sites, this should be false.
 */
define( 'WP_DEBUG', false );

/* Add any custom values between this line and the "stop editing" line. */

// ** HTTPS Settings ** //
// ****** IMPORTANT: Replace 'yourdomain.com' with your actual domain name ******
define( 'WP_HOME', 'http://localhost:SHOP1_PORT_PLACEHOLDER' );
define( 'WP_SITEURL', 'http://localhost:SHOP1_PORT_PLACEHOLDER' );

// ** Filesystem Method ** //
// Force WordPress to use direct file I/O instead of attempting FTP/SSH
define( 'FS_METHOD', 'direct' );


/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';