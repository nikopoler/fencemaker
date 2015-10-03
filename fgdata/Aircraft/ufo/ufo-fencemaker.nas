# dialogs -----------------------------------------------------------------------------------------

var fence_dialog = gui.Dialog.new("/sim/gui/dialogs/ufo/fence/dialog", "Aircraft/ufo/Dialogs/fence.xml");


var export_fenceplan = func {
	var lenghtFace = getprop("/fence/lenght");
	if (lenghtFace == nil){
		printf ("Press f-key and enter lenght of fence.");
		return;
	}
	var widthFace = getprop("/fence/width");
	if (widthFace == nil or widthFace == ''){
		setprop("/fence/width", 0.0);
	}
	widthFace = getprop("/fence/width");
	
	var MaxHeight = func (point, curs_deg){
		var pointRight = geo.Coord.new().set_latlon(point.lat(), point.lon(),0);
		pointRight.apply_course_distance(curs_deg+90, widthFace);
		pointRight.set_alt (geodinfo(pointRight.lat(), pointRight.lon())[0]);
		
		var pointLeft = geo.Coord.new().set_latlon(point.lat(), point.lon(),0);
		pointLeft.apply_course_distance(curs_deg-90, widthFace);
		pointLeft.set_alt (geodinfo(pointLeft.lat(), pointLeft.lon())[0]);
		
		var max = geo.elevation(point.lat(), point.lon());
		if (pointRight.alt() > point.alt()) {max = pointRight.alt();}
		if (pointLeft.alt()  > point.alt()) {max = pointLeft.alt();}
		
		return max;
	}


	var path = getprop("/sim/fg-home") ~ "/Export/ufo-fenceplan-export-" ~ lenghtFace ~ "x" ~ widthFace ~ ".xml";
	var args = props.Node.new({ filename : path });
	var export = args.getNode("data/flightplan", 1);
	
	var waypoints = ufo.modelmgr.get_data().getChildren("model");
	if (!size(waypoints)) {
		printf("Place waypoints!");
		return;
	}

	var first = geo.Coord.new().set_latlon(
		waypoints[0].getNode("latitude-deg").getValue(),
		waypoints[0].getNode("longitude-deg").getValue(),
		waypoints[0].getNode("elevation-ft").getValue() * FT2M);
	var info = export.getChild("info", 1, 1);
	info.getNode("Lat", 1).setValue(first.lat());
	info.getNode("Lon", 1).setValue(first.lon());
	info.getNode("Alt", 1).setValue(first.alt());
	info.getNode("Tile", 1).setValue(geo.tile_path(first.lat(),first.lon()));
	info.getNode("Lenght", 1).setValue(lenghtFace);
	info.getNode("Width", 1).setValue(widthFace);
	forindex (var i; waypoints) {
		if (i>0) {
			var prev = waypoints[i-1];
			var prevGeoCoord = geo.Coord.new().set_latlon(
				prev.getNode("latitude-deg").getValue(),
				prev.getNode("longitude-deg").getValue(),
				prev.getNode("elevation-ft").getValue() * FT2M);
			var from = waypoints[i];
			var fromGeoCoord = geo.Coord.new().set_latlon(
				from.getNode("latitude-deg").getValue(),
				from.getNode("longitude-deg").getValue(),
				from.getNode("elevation-ft").getValue() * FT2M);
			var curs_deg = prevGeoCoord.course_to(fromGeoCoord);
			var curs_rad = curs_deg*math.pi/180;

			var direct_distance = prevGeoCoord.direct_distance_to(fromGeoCoord);
			var dAlt = fromGeoCoord.alt() - prevGeoCoord.alt();
			printf("Direct distance " ~ direct_distance ~ ",    dAlt " ~ dAlt);
			var distance = math.sqrt (direct_distance * direct_distance - dAlt*dAlt);
			
			var items = int ((distance/lenghtFace)+0.5);
			var realLengtFace = distance/items;
			var dlat = (fromGeoCoord.lat() - prevGeoCoord.lat())/items;
			var dlon = (fromGeoCoord.lon() - prevGeoCoord.lon())/items;
			var dlat2 = dlat/2;
			var dlon2 = dlon/2;
			var dx = realLengtFace * math.sin (curs_rad);
			var dy = realLengtFace * math.cos (curs_rad);
			
			#poles
			for(var pick=0; pick < items; pick += 1) {
				var pole = geo.Coord.new().set_latlon(
					prevGeoCoord.lat() + dlat*(pick),
					prevGeoCoord.lon() + dlon*(pick));
				pole.set_alt (geodinfo(pole.lat(), pole.lon())[0]);
				var to = export.getChild("pole", i*1000+pick, 1);
				to.getNode("name", 1).setValue("#" ~ i ~ "-" ~ pick);
				to.getNode("dx", 1).setDoubleValue(dx);
				to.getNode("dy", 1).setDoubleValue(dy);
				to.getNode("alt", 1).setDoubleValue(MaxHeight(pole, curs_deg));
				if (pick==0) { 
					#get altitude of first pole in leg from our own waypoint 
					#to prevent measure cursor.ac height
					to.getNode("alt", 1).setDoubleValue(prevGeoCoord.alt())
				}
				to.getNode("course", 1).setDoubleValue(curs_rad);
			}
			
			#fences
			for(var pick=0; pick < items; pick += 1) {
				var fence = geo.Coord.new().set_latlon(
					prevGeoCoord.lat() + dlat2 + dlat*(pick),
					prevGeoCoord.lon() + dlon2 + dlon*(pick));
				fence.set_alt (geodinfo(fence.lat(), fence.lon())[0]);
				var to = export.getChild("fence", i*1000+pick, 1);
				to.getNode("name", 1).setValue("#" ~ i ~ "-" ~ pick);
				to.getNode("lenght", 1).setDoubleValue(realLengtFace);
				to.getNode("dx", 1).setDoubleValue(dx);
				to.getNode("dy", 1).setDoubleValue(dy);
				to.getNode("alt", 1).setDoubleValue(MaxHeight(fence, curs_deg));
				to.getNode("course", 1).setDoubleValue(curs_rad);
			}
		}
	}

	#add last pole
	var pole = geo.Coord.new().set_latlon(
	waypoints[-1].getNode("latitude-deg").getValue(),
	waypoints[-1].getNode("longitude-deg").getValue(),
	waypoints[-1].getNode("elevation-ft").getValue() * FT2M);
	var to = export.getChild("pole", 1, 1);
	to.getNode("name", 1).setValue("#");
	to.getNode("dx", 1).setDoubleValue(dx);
	to.getNode("dy", 1).setDoubleValue(dy);
	to.getNode("alt", 1).setDoubleValue(pole.alt());
	to.getNode("course", 1).setDoubleValue(curs_rad);

	fgcommand("savexml", args);
	print("fenceplan exported to ", path);
}

