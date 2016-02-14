(function() {
	angular.
	module('tabularazr').
	controller('BrowserCtrl', ['$scope', BrowserCtrl]);

	function BrowserCtrl($scope) {
		$scope.model = {
			message: 'Hello World'
		};

		console.log($scope);
	}
})();