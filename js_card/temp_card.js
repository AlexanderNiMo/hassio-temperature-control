
console.log('read file temp_card');


class ContentCardExample extends HTMLElement {

  setConfig(config) {
    if (!config.config) {
      throw new Error('You need to define a config');
    }
    this.config = config;
  }

  set hass(hass) {
    console.log('set_hass temp_card');

    this._hass = hass

    if (!this.card) {
      this.render_card();
    }

  }

  render_card(){
      this.api = new TemperatureAPI(this.config.config.api_host);
      this.card = document.createElement('ha-card');
      this.card.header = 'Настройки расписания температуры';

      let room_list_label = document.createElement('label');
      room_list_label.innerHTML = 'Выберите помещение:'
      let room_list = document.createElement('select');
      room_list.title = 'Room';
      room_list.addEventListener('change', this.update_current_room.bind(this));
      let rooms = this.api.get_rooms();
      for (let room of rooms){
        let val = document.createElement('option');
        val.value = room;
        val.innerHTML = room;
        room_list.add(val);
      }
      room_list_label.appendChild(room_list);
      this.card.appendChild(room_list_label);

      this.current_room = '';
      if (rooms.length>0){
        this.current_room = rooms[0];
      }

      this.border = document.createElement('hr');
      this.card.appendChild(this.border);
      this.render_room_info();

      let save_button = document.createElement('button');
      save_button.style.padding = '0 16px 16px';
      save_button.innerHTML = "Save";
      save_button.addEventListener("click", this.save_data.bind(this));
      this.card.appendChild(save_button);

      this.appendChild(this.card);
  }

  render_room_info(){
      if (this.current_room === ''){
          return
      }
      if (this.room_el){
          this.card.removeChild(this.room_el);
      }
      this.room_el = this.current_info.render();
      this.card.insertBefore(this.room_el, this.border);
  }

  update_current_room(event){
      this.current_room = event.target.value;
      this.render_room_info();
  }

  get current_info(){
      let room_data = this.api.get_room_info(this.current_room);
      this.room_info = room_info_from_json_data(room_data);
      return this.room_info;
  }

  save_data(){
    this.api.update_room_info(this.current_room, this.room_info);
  }

  getCardSize() {
    console.log('getCardSize temp_card');
    return 30;
  }
}


class TemperatureAPI{

    constructor(api_host) {
        this.api_host = api_host;
    }

    get_full_info(){
        var theUrl = new URL('/full', this.api_host);
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", theUrl, false ); // false for synchronous request
        xmlHttp.send( null );
        return JSON.parse(xmlHttp.responseText)
    }

    get_rooms(){
        let data = this.get_full_info();
        let keys = [];
        for (let key in data){
            keys.push(key)
        }
        return keys;
    }

    get_room_info(room){
        var theUrl = new URL('/', this.api_host);
        theUrl.searchParams.set('room', room);
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", theUrl, false ); // false for synchronous request
        xmlHttp.send( null );
        return JSON.parse(xmlHttp.responseText)
    }

    update_room_info(room, data){
        var theUrl = new URL('/',this.api_host)
        theUrl.searchParams.set('room', room);
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "POST", theUrl, false ); // false for synchronous request
        xmlHttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8")
        xmlHttp.send( JSON.stringify(data) );
        return JSON.parse(xmlHttp.responseText)
    }
}


class RoomInfo{
    constructor(name, working_days, sunday, departure) {
        this.name = name;
        this.working_days = working_days;
        this.sunday = sunday;
        this.departure = departure
    }

    update_name(event){
        this.name = event.target.value
    }

    render(){
        let container = document.createElement('div');
        container.header = 'Room temperature info.';

        let name_container = document.createElement('div');
        let name_label = document.createElement('label');
        name_label.innerHTML = "Комната:";
        let name = document.createElement('input');
        name.value = this.name;
        name.style.margin = "10px 10px";
        name.addEventListener('change', this.update_name.bind(this))
        name_label.appendChild(name)
        name_container.appendChild(name_label)
        container.appendChild(name_container);

        let timetable = document.createElement('div');

        let work_container = document.createElement('div');
        work_container.style.margin = "10px";
        work_container.style.display = "inline-block";
        work_container.style.width = "45%";
        let work_day_label = document.createElement('label');
        work_day_label.innerHTML = "Рабочие дни:";
        let working_days = this.working_days.render();
        work_day_label.appendChild(working_days);
        work_container.appendChild(work_day_label);
        timetable.appendChild(work_container);

        let sunday_container = document.createElement('div');
        sunday_container.style.margin = "10px";
        sunday_container.style.display = "inline-block";
        sunday_container.style.width = "45%";

        let sunday_label = document.createElement('label');
        sunday_label.innerHTML = 'Выходные дни:';
        let sunday = this.sunday.render();
        sunday_label.appendChild(sunday);
        sunday_container.appendChild(sunday_label);
        timetable.appendChild(sunday_container);

        container.appendChild(timetable)

        let departure = this.departure.render();
        departure.style.margin = "10px 10px";
        container.appendChild(departure);
        return container;
    }
}

function room_info_from_json_data(room_data){
    return new RoomInfo(
      room_data.name,
      new DayTemperatureSet(room_data.working_days.time, room_data.working_days.temperature),
      new DayTemperatureSet(room_data.sunday.time, room_data.sunday.temperature),
      new Temperature(room_data.departure.temperature)
  )
}

class DayTemperatureSet{
    constructor(time, temperature) {
        this.time = time;
        this.temperature = temperature;
    }

    get index_title(){
        return [
            'Утро', 'День', 'Вечер', 'Ночь'
        ]
    }

    time_change(event){
        console.log(event);
        this.time[event.target.id] = event.target.value;
    }

    temperature_change(event){
        console.log(event);
        this.temperature[event.target.id] = event.target.value
        let output = event.target.parentElement.getElementsByClassName('output');
        output[0].innerHTML = event.target.value;
    }

    render(){
        let container = document.createElement('div');
        let time = this.render_list(this.time, "Время:", this.time_change.bind(this));
        container.appendChild(time);
        let temperature = this.render_list(this.temperature, "Температура:", this.temperature_change.bind(this))
        container.appendChild(temperature);

        return container
    }

    render_list(data, label_text, func){
        let label = document.createElement('label');
        label.innerHTML = label_text;
        let list = document.createElement('ol');
        list.style.marker = 'none'
        let index_title = this.index_title;
        for (let index in data){
            let el = document.createElement('li');

            let title = document.createElement('label');
            title.innerHTML = index_title[index]
            el.appendChild(title);

            let input = document.createElement('input');
            input.value = data[index];
            input.id = index;
            input.addEventListener('change', func);
            input.style.width = "60%"
            input.style.position = 'right';
            el.appendChild(input);

            if (Number(data[index]) === data[index] ){
                input.type = 'range';
                input.min = "15";
                input.max = "35";
                input.step = "0.5";
                let input_value = document.createElement('output');
                input_value.innerHTML = data[index];
                input_value.style.margin = '1px';
                input_value.className = 'output';
                el.appendChild(input_value);
            }

            list.appendChild(el);
        }
        label.appendChild(list);
        return label
    }

}

class Temperature{
    constructor(temperature) {
        this.temperature = temperature;
    }

    render() {
        let container = document.createElement('div');
        let label = document.createElement('label');
        label.innerHTML = "Температура при отъезде:";
        let temperature = document.createElement('input');
        temperature.value = this.temperature
        temperature.addEventListener('change', this.change_temperature.bind(this))
        temperature.style.width = "60%";
        temperature.style.margin = "10px 10px";
        label.appendChild(temperature);
        container.appendChild(label);
        return container
    }

    change_temperature(event){
        this.temperature = event.target.value;
    }
}

  customElements.define('lovelace-temperature-card', ContentCardExample);
