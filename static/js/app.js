(function() {
	var app = angular.module('tabularazr', ['ui.router','ngMaterial','lfNgMdFileInput']);

	app.config(['$stateProvider', '$urlRouterProvider', '$locationProvider', '$mdThemingProvider', function ($stateProvider, $urlRouterProvider, $locationProvider, $mdThemingProvider) {
    $urlRouterProvider.otherwise('/');

    $locationProvider.html5Mode(true);
    
    $mdThemingProvider.theme('default').primaryPalette('blue');

    $stateProvider.
    state('Home', {
      url: '/',
      templateUrl: '/static/templates/index.tpl.html'
    }).
    state('Browser', {
      url: '/browser?filename&table_id',
      templateUrl: '/static/js/browser/browser.tpl.html',
      controller: 'BrowserCtrl'
    });
  }]);
})();