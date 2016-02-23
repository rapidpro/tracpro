// jsfiddle references
// http://jsfiddle.net/erinw/ukdegfpb/5/
// http://jsfiddle.net/zafrii/4cu28pae/

$(function() {
  var VIVID_COLORS = ['#006837', '#A7082C', '#1F49BF', '#FF8200', '#FFD100'];
  var LIGHT_COLORS = ['#94D192', '#F2A2B3', '#96AEF2', '#FDC690', '#FFFFBF'];

  var getColors = function(categories) {
    var allColors = [];
    // Use the full set of colors, starting with bright colors.
    $.each(VIVID_COLORS, function(i, color) { allColors.push(color); });
    $.each(LIGHT_COLORS, function(i, color) { allColors.push(color); });

    var colors = {};
    $.each(categories, function(i, category) {
      colors[category] = allColors[i];
    });

    return colors;
  }

  $.getJSON( "/boundary/", function( data ) {
    var items = [];
    $.each( data, function( key, val ) {
      all_boundaries = val;
    });

    $('.map').each(function() {
      var map_div = $(this);
      var map_data = map_div.data('map-data');
      var colors = getColors(map_div.data('all-categories'));

      var map = L.map(this.id);

      boundaries_array = [];
      for (data_index in map_data) {
        for (b_index in all_boundaries) {
          if (all_boundaries[b_index].properties.id == map_data[data_index].boundary) {
            all_boundaries[b_index].properties.style.fillColor = colors[map_data[data_index].category];
            mp = all_boundaries[b_index];
            boundaries = new L.GeoJSON(mp, {
              style: function(feature) {
                return feature.properties.style
              }
            });
            boundaries.addTo(map);
            boundaries_array.push(boundaries);
          }
        }
      }

      // Center the map to include all boundaries
      var boundaries_group = new L.featureGroup(boundaries_array);
      map.fitBounds(boundaries_group.getBounds());

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
