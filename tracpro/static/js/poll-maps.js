
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

      // Prevent the user from zooming out any further.
      map.options.minZoom = map.getZoom();

      // Ensure that the zoom out control appears disabled.
      // Leaflet only does this automatically when the user zooms in and then
      // zooms out again.
      var zoomOut = $(map.zoomControl._container).find('.leaflet-control-zoom-out');
      zoomOut.addClass('leaflet-disabled');
    }
    $(window).resize();  // Fix the chart size when map displayed
  });

  /* Info box that will display extra data on boundary hover. */
  var InfoBox = L.Control.extend({
    options: {
      position: 'bottomleft'
    },
    onAdd: function(map) {
      this._container = L.DomUtil.create('div', 'info');
      this.update(null);
      return this._container;
    },
    update: function(feature) {
      var container = $(this._container);
      container.empty();
      if (feature) {
        container.append("<h3>" + feature.properties.name + "</h3>");
        if (feature.data) {
          var dataList = $("<ul>");
          $.each(feature.data, function(key, value) {
            var name = key.replace(/-/g, " ") + ": "  // replace dashes with spaces
            var item = $("<li>");
            item.append($("<span>").addClass("property-name").html(name));
            item.append(value);
            dataList.append(item);
          });
          container.append(dataList);
        } else {
          container.append("<p>No data available for this boundary.</p>");
        }
      } else {
        container.append("<h3>Boundary Data</h3>");
        container.append("<p>Hover over a boundary to see more info.</p>");
      }
    }
  });

  /* Display a legend of category colors. */
  var Legend = L.Control.extend({
    options: {
      position: 'bottomright'
    },
    onAdd: function(map) {
      this._container = L.DomUtil.create('div', 'legend');
      this.update(getColors($(map._container).data('all-categories')));
      return this._container;
    },
    update: function(colors) {
      var legend = $("<ul>");
      $.each(colors, function(category, color) {
        var colorSwatch = $("<span>").addClass("color").css("background-color", color);
        var item = $("<li>").append(colorSwatch).append(category);
        legend.append(item);
      });
      $(this._container).append(legend);
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
            layer.setStyle({fillOpacity: 0.9, weight: 3});
            layer._map.infoBox.update(layer.feature);
          },
          mouseout: function(e) {
            /* Reset the info box when the user stops hovering on this boundary. */
            var layer = e.target;
            layer.setStyle({fillOpacity: 1.0, weight: 2});
            layer._map.infoBox.update();
          }
        });
      },
      style: {
        color: "#eee",
        opacity: 1,
        fillOpacity: 1.0,
        weight: 2
      }
    }
  });

  /* Retrieve boundary data from the server, and create the map. */
  $.getJSON("/boundary/", function(data) {
    var allBoundaries = data['results'];

    $('.map').each(function() {
      var mapDiv = $(this);
      var mapData = mapDiv.data('map-data');  // boundary id -> {'category': 'foo', ...}
      var mapColors = getColors(mapDiv.data('all-categories'));  // category -> display color

      var boundaries = [];
      $.each(allBoundaries, function(boundaryId, boundaryData) {
        var data = mapData[boundaryId] || null;
        var fillColor = data ? mapColors[data.category] : "#c2aa7e";

        // Deep-copy the basic boundary info and augment with map-specific data.
        var info = $.extend(true, {data: data}, boundaryData);
        var boundary = new Boundary(info);
        boundary.setStyle({fillColor: fillColor});
        boundaries.push(boundary);
      });

      var map = L.map(this, {
        attributionControl: false,
        fullscreenControl: {
          position: "topright"
        },
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
