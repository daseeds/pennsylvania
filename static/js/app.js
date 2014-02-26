var supportTouch;
var map;

$(document).ready(function() {
  $(document).on('init.slides', function() {
    $('.loading-container').fadeOut(function() {
      $(this).remove();
    });
  });

  $('#slides').superslides({
    slide_easing: 'easeInOutCubic',
    slide_speed: 800,
    pagination: true,
    hashchange: true,
    scrollable: true
  });

/*  document.ontouchmove = function(e) {
    e.preventDefault();
  };*/
  $('#slides').hammer().on('swipeleft', function() {
    $(this).superslides('animate', 'next');
  });

  $('#slides').hammer().on('swiperight', function() {
    $(this).superslides('animate', 'prev');
  });

  supportTouch = !! ('ontouchstart' in window) || !! ('msmaxtouchpoints' in window.navigator);

});

var manoirLatLng = {
    latLng: new google.maps.LatLng(49.4246006,-1.2569717),
    label: "Le Manoir de Juganville"
}

var service;
var infowindow;

function initialize() {
  var map_canvas = document.getElementById("map-canvas");
  var map_options = {
          center: manoirLatLng.latLng,
          zoom: 14,
          mapTypeId: google.maps.MapTypeId.ROADMAP,
          mapTypeControl: false,
          maxZoom: 20,
          minZoom: 5,
          scrollwheel: false,
          draggable: !supportTouch //turn off draggable when device support touch(such as phone/tablet)
      };
  map = new google.maps.Map(map_canvas, map_options);
  
  var request = {
    reference: 'CnRkAAAAGnBVNFDeQoOQHzgdOpOqJNV7K9-c5IQrWFUYD9TNhUmz5-aHhfqyKH0zmAcUlkqVCrpaKcV8ZjGQKzB6GXxtzUYcP-muHafGsmW-1CwjTPBCmK43AZpAwW0FRtQDQADj3H2bzwwHVIXlQAiccm7r4xIQmjt_Oqm2FejWpBxLWs3L_RoUbharABi5FMnKnzmRL2TGju6UA4k'
  };

  var infowindow = new google.maps.InfoWindow();
  var service = new google.maps.places.PlacesService(map);

  service.getDetails(request, function(place, status) {
    if (status == google.maps.places.PlacesServiceStatus.OK) {
      var marker = new google.maps.Marker({
        map: map,
        position: place.geometry.location
      });
      google.maps.event.addListener(marker, 'click', function() {
        infowindow.setContent(place.name);
        infowindow.open(map, this);
      });
    }
  });

  var iconBase = 'http://google.com/mapfiles/ms/micons/';
  var marker = new google.maps.Marker({
    position:  manoirLatLng.latLng,
    map: map,
    title: "cabinet",
    icon: iconBase + 'blue.png',
    content: "<p>920 Second Avenue S.<br /> Suite 1400 (International Centre II) <br />Minneapolis, MN 55402 <br />612-375-0077<p>Elevator Lobby located to the right of Caf&eacute; Patteen, we are on the 14th floor.</p>"
  });
}

function callback(results, status) {
  if (status == google.maps.places.PlacesServiceStatus.OK) {
    for (var i = 0; i < results.length; i++) {
      var place = results[i];
      createMarker(results[i]);
    }
  }
}
