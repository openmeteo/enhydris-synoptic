var map;

var _setupMarkers = function (data_layers) {
    for (var i = 0; i < enhydris.mapStations.length; i++) {
        station = enhydris.mapStations[i];

        // Circle marker
        L.circleMarker(
            [station.latitude, station.longitude],
            {color: "red", fillColor: "#f03", fillOpacity: 0.5, radius: 5}
        ).addTo(map);

        Object.keys(station.last_values).forEach(function(key) {
            // Rectangle with info
            html = (
                "<strong><a href='" + station.target_url + "'>" + station.name + "</a></strong><br>" +
                "<span class='date " + station.freshness + "'>" + station.last_common_date_pretty_without_timezone + "</span><br>" +
                "<span class='value " + station.last_values_status[key] + "'>" + station.last_values[key] + "</span>"
            )
            icon = L.divIcon({html: html, iconSize: [105, 55], iconAnchor: [108, 58]});
            L.marker([station.latitude, station.longitude], {icon: icon}).addTo(
                data_layers[key]
            );
        });
    }
};


var _setupLayersControl = function (data_layers) {
    L.control.groupedLayers(
        enhydris.mapBaseLayers,
        {"": data_layers},
        {exclusiveGroups: [""]}
    ).addTo(map);
};


var _getDataLayers = function () {
    var layers = {}, first = true;
    for (var i = 0; i < enhydris.mapStations.length; i++) {
        station = enhydris.mapStations[i];
        Object.keys(station.last_values).forEach(function(key) {
            if (key in layers)
                return;
            layers[key] = new L.featureGroup();
            if (first) {
                first = false;
                layers[key].addTo(map);
            }
        });
    }
    return layers;
};


map = enhydris.mapModule.setupMap();
enhydris.mapModule.setupBaseLayer();
var data_layers = _getDataLayers();
_setupLayersControl(data_layers);
_setupMarkers(data_layers);
