
$(function() {

  var COLORS = [
    // vivid colors
    '#006837', '#1F49BF', '#762a83', '#A7082C', '#FF8200', '#FFD100',
    // light colors
    '#94D192', '#92c5de', '#c2a5cf', '#F2A2B3', '#f7cca0', '#FFFFBF' ];

  /* Associate categories with colors. */
  var getColors = function(categories) {
    var colors = {};
    $.each(categories, function(i, category) {
      colors[category] = COLORS[i % COLORS.length];
    });
    return colors;
  }

  /* Center map to include all boundaries whenever a map tab is opened. */
  $("body").on("shown.bs.tab", function(e) {
    var mapDiv = $($(e.target).attr('href')).find('.map');
    if (mapDiv.length) {
      var map = mapDiv.data('map');
      map.fitBounds(map.boundaries.getBounds());
      map.options.minZoom = map.getZoom();
    }
  });

  /* Info box that will display extra data on boundary hover. */
  var InfoBox = L.Control.extend({
    options: {
      position: 'bottomleft'
    },
    onAdd: function(map) {
      this._div = L.DomUtil.create('div', 'info');
      this.update();
      return this._div;
    },
    update: function(properties) {
      this._div.innerHTML = '<h3>Boundary Data</h3>';
      if (properties) {
        this._div.innerHTML += "<h4>" + properties.name + "</h4>";
        this._div.innerHTML += "<h5>Category: " + properties.category + "</h5>";
      } else {
        this._div.innerHTML += "<h4>Hover over a boundary</h4>";
        this._div.innerHTML += "<h5>&nbsp;</h5>";
      }
    }
  });

  /* Display a legend of category colors. */
  var Legend = L.Control.extend({
    options: {
      position: 'bottomright'
    },
    onAdd: function(map) {
      var items = [];
      var colors = getColors($(map._container).data('all-categories'));
      for (var category in colors) {
        var color = colors[category];
        var item = '<div class="legend_color" style="background: ' + color + ';"></div>';
        item += "<span>" + category + "</span>";
        items.push(item);
      }

      var legend = L.DomUtil.create('div', 'info legend');
      legend.innerHTML = items.join("<br>");
      return legend;
    }
  });

  /* Display a geographic boundary on the map. */
  var Boundary = L.GeoJSON.extend({
    options: {
      onEachFeature: function(feature, layer) {
        layer.on({
          mouseover: function(e) {
            /* Add boundary data to the info box when the user hovers on this boundary. */
            var layer = e.target;
            layer.setStyle({weight: 6});
            layer._map.infoBox.update(layer.feature.properties);
          },
          mouseout: function(e) {
            /* Reset the info box when the user stops hovering on this boundary. */
            var layer = e.target;
            layer.setStyle({weight: 2});
            layer._map.infoBox.update();
          }
        });
      }
    }
  })

  /* Retrieve boundary data from the server, and create the map. */
  $.getJSON("/boundary/", function(data) {
    var allBoundaries = data['results'];

    $('.map').each(function() {
      var mapDiv = $(this);

      var boundaries = [];
      var colors = getColors(mapDiv.data('all-categories'));
      $.each(mapDiv.data('map-data'), function(boundaryId, category) {
        if (boundaryId in allBoundaries) {
          // Create a deep copy of the boundary info from the server
          var boundaryInfo = $.extend(true, {}, allBoundaries[boundaryId]);

          boundaryInfo.properties.category = category || "None";
          boundary = new Boundary(boundaryInfo, {
            style: {
              'color': '#fff',
              'opacity': 1,
              'fillColor': colors[category],
              'fillOpacity': 1,
              'weight': 2
            }
          });
          boundaries.push(boundary);
        }
      });

      var map = L.map(this, {
        scrollWheelZoom: false,
        maxBoundsViscosity: 1  // prevent scrolling out of bounds
      });

      map.infoBox = new InfoBox();
      map.addControl(map.infoBox);

      map.legend = new Legend();
      map.addControl(map.legend);

      map.boundaries = L.featureGroup(boundaries);
      map.addControl(map.boundaries);
      map.setMaxBounds(map.boundaries.getBounds());

      mapDiv.data('map', map);
    });
  });
});
