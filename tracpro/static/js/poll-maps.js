
$(function() {

  var VIVIDCOLORS = ['#006837', '#A7082C', '#1F49BF', '#FF8200', '#FFD100', '#40004b', '#762a83', '#1b7837'];
  var LIGHTCOLORS = ['#94D192', '#F2A2B3', '#96AEF2', '#FFFFBF', '#c2a5cf', '#a6dba0', '#92c5de'];

  var getColors = function(categories) {
    var allColors = [];
    // Use the full set of colors, starting with bright colors.
    $.each(VIVIDCOLORS, function(i, color) { allColors.push(color); });
    $.each(LIGHTCOLORS, function(i, color) { allColors.push(color); });
    // Double this set of colors using the same colors for questions with many categories
    $.each(allColors, function(i, color) { allColors.push(color); });

    var colors = {};
    $.each(categories, function(i, category) {
      colors[category] = allColors[i];
    });

    return colors;
  }

  $.getJSON( "/boundary/", function( data ) {
    var allBoundaries = {};
    for (var i in data['results']) {
      var boundaryInfo = data['results'][i];
      allBoundaries[boundaryInfo.properties.id] = boundaryInfo;
    }

    $('.map').each(function() {
      var map_div = $(this);
      var mapData = map_div.data('map-data');
      var colors = getColors(map_div.data('all-categories'));

      var map = L.map(this.id);

      // Info box
      // Display information on boundary hover
      var info = L.control({
          position: 'bottomleft'
      });

      info.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'info');
        this.update();
        return this._div;
      };

      info.update = function (props) {
        this._div.innerHTML = '<h3>Boundary Data</h3>' +  (props ?
          '<h4>' + props.name + '</h4>' + '<h5>Category: ' + props.category + '</h5>'
          : '<h4>Hover over a boundary</h4><h5>&nbsp;</h5>');
      };

      info.addTo(map);

      function highlightFeature(e) {
        var layer = e.target;

        layer.setStyle({
            weight: 6
        });

        info.update(layer.feature.properties);
      }

      function resetHighlight(e) {
        var layer = e.target;
          layer.setStyle({
              weight: 2
          });
        info.update();
      }

      function onEachFeature(feature, layer) {
          layer.on({
            mouseover: highlightFeature,
            mouseout: resetHighlight
          });
      }

      var boundariesArray = [];
      for (var boundaryId in mapData) {
        if (boundaryId in allBoundaries) {
          var category = mapData[boundaryId];
          var boundaryInfo = $.extend({}, allBoundaries[boundaryId]);
          boundaryInfo.properties = $.extend({}, boundaryInfo.properties);
          boundaryInfo.properties.style = {
            'color': '#fff',
            'opacity': 1,
            'fillColor': colors[category],
            'fillOpacity': 1,
            'weight': 2
          }
          boundaryInfo.properties.category = category;
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
      map_div.data('boundary-array', boundariesArray);

      // Center the map to include all boundaries
      var boundaries_group = new L.featureGroup(map_div.data('boundary-array'));
      map.fitBounds(boundaries_group.getBounds());

      // Add legend to bottom-right corner
      var legend = L.control({
          position: 'bottomright'
      });
      legend.onAdd = function (map) {

          var colors = getColors(map_div.data('all-categories'));
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
    $(".visual .map").hide(); // hide maps on initial page load, after they are drawn
  });

  $(".tab_chart").click(function(){
    $(this).closest("div").find('.map').hide();
    $(this).closest("div").find("div[class^='chart-']").show();
    $(this).parent().addClass('active');
    $(this).parent().parent().find(".tab_map").parent().removeClass('active');
  });

  $(".tab_map").click(function(){
    $(this).closest("div").find('.map').show();
    $(this).closest("div").find("div[class^='chart-']").hide();
    $(this).parent().addClass('active');
    $(this).parent().parent().find(".tab_chart").parent().removeClass('active');
  });
});
