'use strict';

/** Same as flaskr.config.STATIC_PROJECT_VERSION */
const version = '0.1';

/** Directory of the JS files used in prod. */
const js_dest = `./dist-${version}/js/`;

/** Directory of the fonts used in prod. */
const fonts_dest = `./dist-${version}/webfonts/`;

/** Directory of the images used in prod by jQuery UI. */
const jquery_ui_icons_dest = `./dist-${version}/css/images/`;

var vendor_scripts = [
    {
        name: 'visitor_space',
        scripts: [
            './jquery-3.5.1.min.js',
            './popper.min.js',
            './bootstrap-4.5.2/js/bootstrap.min.js',
            './zoom-1.7.21/jquery.zoom.min.js',
            './intersection-observer.js',
            './scrollama-2.2.0.min.js',
        ]
    },
    {
        name: 'admin_space',
        scripts: [
            './jquery-3.5.1.min.js',
            './jquery-ui-1.12.1/jquery-ui.min.js',
            './popper.min.js',
            './bootstrap-4.5.2/js/bootstrap.min.js',
            './zoom-1.7.21/jquery.zoom.min.js',
            './intersection-observer.js',
            './scrollama-2.2.0.min.js',
            './chart-2.9.3.bundle.min.js',
            './tiff.min.js',
            './marked.min.js',
        ]
    },
    {
        name: 'map_viewer',
        scripts: [
            './jquery-3.5.1.min.js',
            './popper.min.js',
            './jquery-ui-1.12.1/jquery-ui.min.js',
            './ol-6.4.3.js',
            './chart-2.9.3.bundle.min.js',
            './lz-string/libs/lz-string.min.js',
        ]
    },
];

var app_scripts = [
    {
        name: 'visitor_space',
        scripts: [
            './sentry_handler.js',
            './config.js',
            './main.js',
            './background_animation.js',
            './social_timelines.js',
        ]
    },
    {
        name: 'admin_space',
        scripts: [
            './sentry_handler.js',
            './config.js',
            './main.js',
            './background_animation.js',
            './social_timelines.js',
            './admin.js',
        ]
    },
    {
        name: 'storytelling_map',
        scripts: [
            './storytelling_map.js',
        ]
    },
    {
        name: 'map_viewer',
        scripts: [
            './sentry_handler.js',
            './map_viewer.js',
        ]
    },
];

var gulp = require('gulp');
var less = require('gulp-less');
var cssnano = require('gulp-cssnano');
var sourcemaps = require('gulp-sourcemaps');
var LessAutoprefix = require('less-plugin-autoprefix');
var autoprefix = new LessAutoprefix({ browsers: ['last 2 versions'] });
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var babel = require('gulp-babel');
var notify = require("gulp-notify");
var changed = require('gulp-changed');
const removeUseStrict = require("gulp-remove-use-strict");

gulp.task('alert_style', function() {
    return gulp.src('.')
        .pipe(notify("Style tasks done."));
});

gulp.task('icons', function() {
    return gulp.src('./node_modules/@fortawesome/fontawesome-free/webfonts/*')
        .pipe(changed(fonts_dest))
        .pipe(gulp.dest(fonts_dest)); // copy fonts to dist
});

gulp.task('jquery_ui_images', function() {
    return gulp.src('./jquery-ui-1.12.1/images/*')
        .pipe(changed(jquery_ui_icons_dest))
        .pipe(gulp.dest(jquery_ui_icons_dest)); // copy the jQuery UI icon set
});

gulp.task('styles', function () {
    return gulp.src('./*.less')
        .pipe(sourcemaps.init())
        .pipe(less({ plugins: [autoprefix] })) // compile the Less files with the autoprefix plugin
        .pipe(cssnano()) // minify CSS
        .pipe(sourcemaps.write('./')) // source maps in the same directory as the compiled CSS files
        .pipe(gulp.dest('./dist-' + version + '/css/')) // compiled CSS directory
        .pipe(notify({
            onLast: true, // only happen on the last file of the stream (skip the map file notification)
            title: "Style tasks done",
            message: "CSS bundle files generated"
        }))
});
gulp.watch('./*.less', gulp.series('styles'));

vendor_scripts.forEach(function(element) {
    gulp.task(element.name + '_vendor_scripts', function () {
        return gulp.src(element.scripts)
            .pipe(sourcemaps.init())
            .pipe(concat(element.name + '.vendor.bundle.js'))
            .pipe(uglify())
            .pipe(sourcemaps.write('.'))
            .pipe(gulp.dest(js_dest))
            .pipe(notify({
                onLast: true,
                title: "Updated <%= file.relative %>",
                message: "JS bundle file generated"
            }));
    });
    gulp.watch(element.scripts, gulp.series(element.name + '_vendor_scripts'));
});

app_scripts.forEach(function(element) {
    gulp.task(element.name + '_app_scripts', function () {
        return gulp.src(element.scripts)
            .pipe(sourcemaps.init())
            .pipe(babel({
                presets: ['@babel/env'],
                plugins: ['@babel/plugin-proposal-class-properties'],
            }))
            .pipe(removeUseStrict({
                force: true // remove "use strict"; regardless of whether it appears as a directive prologue
            }))
            .pipe(concat(element.name + '.app.bundle.js'))
            .pipe(uglify())
            .pipe(sourcemaps.write('.'))
            .pipe(gulp.dest(js_dest))
            .pipe(notify({
                onLast: true,
                title: "Updated <%= file.relative %>",
                message: "JS bundle file generated"
            }));
    });
    gulp.watch(element.scripts, gulp.series(element.name + '_app_scripts'));
});

gulp.task('default', gulp.parallel(
    'icons',
    'jquery_ui_images'
    )
);
