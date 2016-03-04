
$(function() {

  var COLORS = [
    // vivid colors
    '#006837', '#1F49BF', '#762a83', '#A7082C', '#FF8200', '#FFD100',
    // light colors
    '#94D192', '#92c5de', '#c2a5cf', '#F2A2B3', '#f7cca0', '#FFFFBF' ];

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
      var boundariesGroup = mapDiv.data('boundary-array');
      map.fitBounds(L.featureGroup(boundariesGroup).getBounds());
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

  $.getJSON("/boundary/", function(data) {
    var allBoundaries = data['results'];

    $('.map').each(function() {
      var mapDiv = $(this);
      var map = L.map(this, {
        'scrollWheelZoom': false
      });

      var info = new InfoBox();
      info.addTo(map);

      function onEachFeature(feature, layer) {
        layer.on({
          mouseover: function (e) {
            /* Add info about the boundary to the info box. */
            var layer = e.target;
            layer.setStyle({weight: 6});
            info.update(layer.feature.properties);
          },
          mouseout: function (e) {
            /* Reset the info box. */
            var layer = e.target;
            layer.setStyle({weight: 2});
            info.update();
          }
        });
      }

      var boundariesArray = [];
      var mapData = mapDiv.data('map-data');
      var colors = getColors(mapDiv.data('all-categories'));
      for (var boundaryId in mapData) {
        if (boundaryId in allBoundaries) {
          var category = mapData[boundaryId];
          var boundaryInfo = $.extend(true, {}, allBoundaries[boundaryId]);  // deep copy
          boundaryInfo.properties.style = {
            'color': '#fff',
            'opacity': 1,
            'fillColor': colors[category],
            'fillOpacity': 1,
            'weight': 2
          }
          if (category) {
            boundaryInfo.properties.category = category;
          }
          else {
            boundaryInfo.properties.category = "None";
          }
          boundary = new L.GeoJSON(boundaryInfo, {
            style: function(feature) {
              return feature.properties.style;
            },
            onEachFeature: onEachFeature
          });
          boundary.addTo(map);
          boundariesArray.push(boundary);
        }
      }
      mapDiv.data('boundary-array', boundariesArray);
      mapDiv.data('map', map);

      // Add legend to bottom-right corner
      var legend = L.control({
          position: 'bottomright'
      });
      legend.onAdd = function (map) {
        var colors = getColors(mapDiv.data('all-categories'));
        var div = L.DomUtil.create('div', 'info legend');
        var label = ['<strong>index</strong>'];
        for (key in colors) {
          div.innerHTML += label.push(
            '<div class="legend_color" style="background:' + colors[key] + '"></div><span>' + key + '</span>');
        }

        div.innerHTML = label.join('<br>');
        return div;
      };
      legend.addTo(map);
    });
  });
});
