(function() {
	angular.
	module('tabularazr').
	directive('tabularazrBrowser', BrowserDirective);

	function BrowserDirective() {
		return {
			restrict: 'E',
			controller: 'BrowserCtrl',
			templateUrl: './static/js/browser/browser.tpl.html',
			link: function($scope) {
				$scope.model = {
					message: 'Hello World'
				};
			}
		}
	}
})();