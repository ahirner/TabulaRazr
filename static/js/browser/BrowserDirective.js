(function() {
	angular.
	module('tabularazr').
	directive('browser', BrowserDirective);

	function BrowserDirective() {
		return {
			restrict: 'E',
			replace: true,
			templateUrl: './static/js/browser/browser.tpl.html'
		}
	}
})();