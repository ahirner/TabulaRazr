Browser = React.createClass({
  getInitialState() {
    //TODO: obviously this is dumb, will look into better architecture.
    this.getTables();

    return {
      tables: [],
      activeTable: null
    }
  },

  getTables() {
    return HTTP.call("GET","http://0.0.0.0:7081/api/get_similar_tables_all/muni_bonds/2012_msw_dat_tbls/1648", {},
      (error, result) => {
        if (!error) {
          var data = JSON.parse(result.content);
          var mappedData = data.map(function(dataItem) {
          	var map = {};
          	map[dataItem._id.table_id] = dataItem;
          	return map;
          });

          console.log(mappedData);

          this.setState({tables: JSON.parse(result.content)});
        }
      }
    );
  },

  handleTableLinkClick(id, event) {
  	this.setState({
  		activeTable: parseInt(id)
  	});
  },
 
  renderTableLinks() {
    if (!this.state.tables.length) {
      return <li>Unfortunately, we could not retrieve any tables.</li>;
    } else {
      return this.state.tables.map((table, i) => {
				var onClick = this.handleTableLinkClick.bind(this, table._id.table_id);

        return <TableLink table={table} key={table._id.table_id} onClick={onClick} />;
      });
    }
  },

  renderTable(id) {
  	console.log(id);
  },
 
  render() {
    return (
      <div className="container">
        <div className="left">
          <h3>Similar Tables in Project</h3>
          <ul>
            {this.renderTableLinks()}
          </ul>
        </div>

        <div className="right">
        	<h3>Viewing Table: {this.state.activeTable || 'No Selection'}</h3>

        	{this.renderTable(this.state.activeTable)}
        </div>
      </div>
    );
  }
});