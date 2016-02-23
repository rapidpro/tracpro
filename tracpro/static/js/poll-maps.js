// jsfiddle references
// http://jsfiddle.net/erinw/ukdegfpb/5/
// http://jsfiddle.net/zafrii/4cu28pae/

$(function() {
  $.getJSON( "/boundary/", function( data ) {
    var items = [];
    $.each( data, function( key, val ) {
      all_boundaries = val;
    });

    $('.map').each(function() {
      var map_div = $(this);
      var map_data = map_div.data('maps');
      var colors = map_div.data('colors');

      var map = L.map(this.id);

      boundaries_array = [];
      for (data_index in map_data) {
        for (b_index in all_boundaries) {
          if (all_boundaries[b_index].properties.id == map_data[data_index].boundary) {
            all_boundaries[b_index].properties.style.fillColor = map_data[data_index].color;
            mp = all_boundaries[b_index];
            boundaries = new L.GeoJSON(mp, {
              style: function(feature) {
                return feature.properties.style
              }
            });
            console.log(boundaries);
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

          var colors = map_div.data('colors')
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
