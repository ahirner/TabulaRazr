Table = React.createClass({
  propTypes: {
    table: React.PropTypes.object.isRequired
  },

  renderHeaders() {
  	return this.props.table.meta.map((header, i) => {
			return <th key={"header-" + i}>{header.value}</th>
		})
  },

  renderCells(row, ri) {
  	return this.props.table.meta.map((cell, ci) => {
  		console.log(row[cell.value].value);
			return <td key={"row-" + ri + "-cell-" + ci}>Data</td>;
		});
  },

  renderRows() {
  	return this.props.table.data.forEach((row, ri) => {
  		return <tr key={"row-" + ri}>Row {this.renderCells(row, ri)}</tr>;
  	});
  },

  render() {
    return (
    	<div>
	    	<h3>{this.props.table.header}</h3>

				<table className="browser-table" width="100%">
		      <thead>
		        <tr>
		          {this.renderHeaders()}
		        </tr>
		      </thead>
		      <tbody>
		      	{this.renderRows()}
		      </tbody>
		    </table>
	    </div>
    );
  }
});