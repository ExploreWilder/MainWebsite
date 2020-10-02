const package_info = require('./package.json');

console.log(`
* Project:               ${package_info.name}
* Description:           ${package_info.description}
* Static Assets Version: ${package_info.version}
`.trim());

/** Find out the version from the package configuration. */
const dist_dir = `./dist-${package_info.version}`;

/** Directory of the JS files used in prod. */
const js_dest = `${dist_dir}/js/`;

/** Directory of the CSS files used in prod. */
const css_dest = `${dist_dir}/css/`;

/** Directory of the fonts used in prod. */
const fonts_dest = `${dist_dir}/webfonts/`;

/** Directory of the images used in prod by jQuery UI. */
const jquery_ui_icons_dest = `${dist_dir}/css/images/`;

var vendor_scripts = [
    {
        name: 'visitor_space',
        scripts: [
            './vendor/jquery-3.5.1.min.js',
            './vendor/popper.min.js',
            './vendor/bootstrap-4.5.2/js/bootstrap.min.js',
            './node_modules/jquery-zoom/jquery.zoom.min.js',
            './node_modules/intersection-observer/intersection-observer.js',
            './node_modules/scrollama/build/scrollama.min.js',
        ]
    },
    {
        name: 'admin_space',
        scripts: [
            './vendor/jquery-3.5.1.min.js',
            './vendor/jquery-ui-1.12.1/jquery-ui.min.js',
            './vendor/popper.min.js',
            './vendor/bootstrap-4.5.2/js/bootstrap.min.js',
            './node_modules/jquery-zoom/jquery.zoom.min.js',
            './node_modules/intersection-observer/intersection-observer.js',
            './node_modules/scrollama/build/scrollama.min.js',
            './node_modules/chart.js/dist/Chart.bundle.min.js',
            './node_modules/tiff.js/tiff.min.js',
            './node_modules/marked/marked.min.js',
        ]
    },
    {
        name: 'map_viewer',
        scripts: [
            './vendor/jquery-ui-1.12.1/jquery-ui.min.js',
            './vendor/ol-6.4.3.js',
            './node_modules/chart.js/dist/Chart.bundle.min.js',
            './vendor/webtrack.min.js',
        ]
    },
    {
        name: 'map_player',
        scripts: [
            './vendor/jquery-ui-1.12.1/jquery-ui.min.js',
            // use a custom vts-browser.min.js: '//cdn.melown.com' changed to 'https://cdn.melown.com' to enforce a secure connection
            './vendor/vts-browser.min.js',
            './node_modules/chart.js/dist/Chart.bundle.min.js',
            './vendor/webtrack.min.js',
        ]
    }
];

var app_scripts = [
    {
        name: 'visitor_space',
        scripts: [
            './app/scripts/sentry_handler.js',
            './app/scripts/config.js',
            './app/scripts/main.js',
            './app/scripts/background_animation.js',
            './app/scripts/social_timelines.js',
        ]
    },
    {
        name: 'admin_space',
        scripts: [
            './app/scripts/sentry_handler.js',
            './app/scripts/config.js',
            './app/scripts/main.js',
            './app/scripts/background_animation.js',
            './app/scripts/social_timelines.js',
            './app/scripts/admin.js',
        ]
    },
    {
        name: 'storytelling_map',
        scripts: [
            './app/scripts/storytelling_map.js',
        ]
    },
    {
        name: 'map_viewer',
        scripts: [
            './app/scripts/map_utils.js',
            './app/scripts/map_viewer.config.js',
            './app/scripts/map_viewer.js',
        ]
    },
    {
        name: 'map_player',
        scripts: [
            './app/scripts/map_utils.js',
            './app/scripts/map_player.js',
        ]
    }
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
var notify = require('gulp-notify');
var changed = require('gulp-changed');
var rename = require('gulp-rename');
const removeUseStrict = require('gulp-remove-use-strict');

var all_root_tasks = ['default', 'styles'];

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
    return gulp.src('./vendor/jquery-ui-1.12.1/images/*')
        .pipe(changed(jquery_ui_icons_dest))
        .pipe(gulp.dest(jquery_ui_icons_dest)); // copy the jQuery UI icon set
});

gulp.task('styles', function () {
    return gulp.src('./app/styles/*.less')
        .pipe(sourcemaps.init())
        .pipe(less({
            plugins: [autoprefix]
        })) // compile the Less files with the autoprefix plugin
        .pipe(cssnano({
            zindex: false // don't change my z-index values
        })) // minify CSS
        .pipe(sourcemaps.write('./')) // source maps in the same directory as the compiled CSS files
        .pipe(gulp.dest(css_dest)) // compiled CSS directory
        .pipe(notify({
            onLast: true, // only happen on the last file of the stream (skip the map file notification)
            title: "Style tasks done",
            message: "CSS bundle files generated"
        }))
});
gulp.watch('./app/styles/*.less', gulp.series('styles'));

gulp.task('sentry', function() {
    return gulp.src('./node_modules/@sentry/browser/build/bundle.min.js')
        .pipe(rename("sentry.js"))
        .pipe(changed(js_dest))
        .pipe(gulp.dest(js_dest));
});

gulp.task('vts_config', function() {
    return gulp.src('./app/scripts/map_player.config.json')
        .pipe(changed(js_dest))
        .pipe(gulp.dest(js_dest));
});

gulp.task('mapbox_style', function() {
    return gulp.src('./node_modules/mapbox-gl/dist/mapbox-gl.css')
        .pipe(changed(css_dest))
        .pipe(gulp.dest(css_dest));
});

gulp.task('vts_style', function() {
    return gulp.src('./vendor/vts-browser.min.css')
        .pipe(changed(css_dest))
        .pipe(gulp.dest(css_dest));
});

gulp.task('mapbox_script', function() {
    return gulp.src('./node_modules/mapbox-gl/dist/mapbox-gl.js')
        .pipe(changed(js_dest))
        .pipe(gulp.dest(js_dest));
});

vendor_scripts.forEach(function(element) {
    const task_name = element.name + '_vendor_scripts';
    gulp.task(task_name, function () {
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
    all_root_tasks.push(task_name);
    gulp.watch(element.scripts, gulp.series(task_name));
});

app_scripts.forEach(function(element) {
    const task_name = element.name + '_app_scripts';
    gulp.task(task_name, function () {
        return gulp.src(element.scripts)
            .pipe(sourcemaps.init())
            .pipe(babel({
                presets: ['@babel/preset-env'],
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
    all_root_tasks.push(task_name);
    gulp.watch(element.scripts, gulp.series(task_name));
});

gulp.task('default', gulp.parallel(
    'icons',
    'jquery_ui_images',
    'sentry',
    'vts_config',
    'mapbox_style',
    'vts_style',
    'mapbox_script',
    )
);

gulp.task('run-all', gulp.parallel(all_root_tasks));
