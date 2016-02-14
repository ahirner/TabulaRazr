(function() {
	var app = angular.module('tabularazr', ['ui.router','ngMaterial','lfNgMdFileInput','ngFileUpload']);

	app.config(['$stateProvider', '$urlRouterProvider', '$locationProvider', '$mdThemingProvider', function ($stateProvider, $urlRouterProvider, $locationProvider, $mdThemingProvider) {
    $urlRouterProvider.otherwise('/');

    $locationProvider.html5Mode(true);
    
    $mdThemingProvider.theme('default').primaryPalette('blue');

    $stateProvider.
    state('Home', {
      url: '/',
      templateUrl: '/static/templates/index.tpl.html',
      controller: 'HomeCtrl'
    }).
    state('Browser', {
      url: '/browser',
      templateUrl: '/static/js/browser/browser.tpl.html',
      controller: 'BrowserCtrl'
    });
  }]);
})();