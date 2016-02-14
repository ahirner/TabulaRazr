(function() {
	var app = angular.module('tabularazr', ['ui.router']);

	app.config(['$stateProvider', '$urlRouterProvider', '$locationProvider', function ($stateProvider, $urlRouterProvider, $locationProvider) {
    $urlRouterProvider.otherwise('/');

    $locationProvider.html5Mode(true);

    $stateProvider.
    state('Home', {
      url: '/',
      templateUrl: '/static/templates/index.tpl.html'
    }).
    state('Browser', {
      url: '/browser',
      templateUrl: '/static/js/browser/browser.tpl.html'
    });
  }]);
})();