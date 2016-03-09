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
          var data = JSON.parse(result.content),
          		map = {};

          data.forEach((item, i) => {
          	map[item._id.table_id] = item;
          });

          this.setState({tables: JSON.parse(result.content), map: map});
        }
      }
    );
  },

  handleTableLinkClick(id, event) {
  	this.setState({
  		activeTableId: parseInt(id)
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
  	if (id) {
  		return <Table key={id} table={this.state.map[id]} />;
  	} else {
  		return <h3>Select a table to display, friend</h3>;
  	}
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
        	<h3>Viewing Table: {this.state.activeTableId || 'No Selection'}</h3>

        	{this.renderTable(this.state.activeTableId)}
        </div>
      </div>
    );
  }
});