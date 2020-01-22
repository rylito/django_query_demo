"use strict"

function Report(container_id, config){
    let $container = $('#' + container_id)

    const KEY_TEXT_MAP = {
        'including_0': '0 reported is significant and counted',
        'excluding_0': '0 reported is NOT significant and NOT counted',
    }

    function format_result(result, is_money){
        if(typeof result === 'number'){
            let formatted = result.toLocaleString('en', {useGrouping:true})
            if(is_money){
                formatted = '$' + formatted
            }
            return formatted
        }
        else if($.isArray(result)){
            let str = ''
            result.forEach(function(item, i){
                if(i !== 0){
                    str += ', '
                }
                str += item
            })
            return str
        }
        return result
    }

    function render_query_result($elem, key, result, is_money, raw, time){
        let key_text = KEY_TEXT_MAP[key]
        console.log(key, key_text)
        let $query_result = e('div',
            key_text ? e('h5', {'style':{'margin-top': '1em'}},key_text) : null,
            e('div', {'style': {'font-weight':'bold', 'font-size': '2em', 'color': '#315184'}}, format_result(result, is_money)),
            e('h6', 'Raw Query'),
            e('pre', {'style': {'overflow':'auto'}}, raw || '[not available]'),
            e('h6', 'Time'),
            e('div', time || '[not available]')
        )
        $elem.append($query_result)
    }

    function fetch_result(url, is_money, $elem){
        $.getJSON(url, function(data){
            console.log(data)
            let data_query = data['query']
            if(typeof data_query === 'object' && !$.isArray(data_query)){
                let query_count = 0
                for(const k in data_query){
                    if(!data_query.hasOwnProperty(k)){continue}
                    let stats_data = data['stats'][query_count]

                    // some queries are not returning stats for some reason. Handle this gracefully so the other
                    // data displays
                    let sql = null
                    let time = null
                    if(stats_data){
                        sql = stats_data['sql']
                        time = stats_data['time']
                    }
                    render_query_result($elem, k, data_query[k], is_money, sql, time)
                    query_count++
                }
            }
            else{
                let stats_data = data['stats'][0]
                render_query_result($elem, null, data['query'], is_money, stats_data['sql'], stats_data['time'])
            }
        })
    }

    config.forEach(function(config_item, index){
        let $results_container, $div = e('div', {'style': {'border': 'solid 1px', 'padding': '1em'}},
            e('h3', (index + 1) + '. ' + config_item['title']),
            e('p', config_item['descrip']),
            $results_container = e('div')
        )
        $container.append($div)

        let is_money = config_item['is_money']
        fetch_result(config_item['url'], is_money, $results_container)
    })
}




