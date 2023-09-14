from jinja2 import Template

def exe_move_item_up(instance):
    # Get the current index
    index = instance.waypoints.currentIndex()

    # Check if the current index is not the first index
    if index.row() > 0:
        # Get the item to move
        item = instance.model.takeRow(index.row())

        # Move the item to the new index
        instance.model.insertRow(index.row() - 1, item)

        # Set the current index to the new index
        instance.waypoints.setCurrentIndex(instance.model.indexFromItem(item[0]))


def exe_move_item_down(instance):
    # Get the current index
    index = instance.waypoints.currentIndex()

    # Check if the current index is not the last index
    if index.row() < instance.model.rowCount() - 1:
        # Get the item to move
        item = instance.model.takeRow(index.row())

        # Move the item to the new index
        instance.model.insertRow(index.row() + 1, item)

        # Set the current index to the new index
        instance.waypoints.setCurrentIndex(instance.model.indexFromItem(item[0]))


def exe_delete_item(instance):
    # Get the current index
    index = instance.waypoints.currentIndex()

    # Remove the item from the model
    instance.model.removeRow(index.row())

def exe_pointing(instance): ## 경로 지우는 용도로 써야겠다
    if instance.on_record == False:
        instance.on_record = True
        instance.btn_pointing.setText("Pointing STOP")
        return
    elif instance.on_record == True:
        instance.btn_pointing.setText("Pointing START")

    instance.on_record = False
    js = """
            for (var i = 0; i < pointsArray.length; i++) {
                {{map}}.removeLayer(pointsArray[i]);
            }
            pointsArray = [];
        """
    instance.view.page().runJavaScript(Template(js).render(map=instance.m.get_name()))
    
def exe_draw_ship(instance):
    if not instance.flag_simulation:
        try:
            lat = float(instance.sensor_data['latitude'])
            lon = float(instance.sensor_data['longitude'])
            head = float(instance.sensor_data['heading']) if instance.sensor_data['heading'] != None else 0
        except:
            return print("here")
    else:
        lat = instance.simulation_lat
        lon = instance.simulation_lon
        head = instance.simulation_head

    ship_size = 0.0105 ## km단위

    triangle1, triangle2, triangle3 = instance.calculate_triangle_vertices(lat, lon, head, ship_size)
    latitude1, longitude1 = triangle1
    latitude2, longitude2 = triangle2
    latitude3, longitude3 = triangle3
    instance.view.page().runJavaScript(Template("{{map}}.removeLayer(polygon)").render(map = instance.m.get_name()))

    js = Template(
        """
        var polygon = L.polygon([
            [{{latitude}}, {{longitude}}],
            [{{latitude2}}, {{longitude2}}],
            [{{latitude3}}, {{longitude3}}]
        ],
        {
            "color": "#000000",
            "weight": 3,
            "opacity": 1,
            "fillColor": "#ff0000",
            "fillOpacity": 1,
            "zIndex": 1000
        }
        ).addTo({{map}});
        """
    ).render(map=instance.m.get_name(), latitude=latitude1, longitude=longitude1,
             latitude2=latitude2, longitude2=longitude2,
             latitude3=latitude3, longitude3=longitude3)

    instance.view.page().runJavaScript(js)