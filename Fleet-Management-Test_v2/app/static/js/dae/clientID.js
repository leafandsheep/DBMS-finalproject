//產生UUID
function generateUUID() { // Public Domain/MIT
    var d = new Date().getTime();
    if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
        d += performance.now(); //use high-precision timer if available
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}
var clientID = { ID: "" };
// 根據系統角色創建ID
if (role == "Cloud") {
    clientID.ID = 'Cloud' + generateUUID();
} else {
    clientID.ID= 'Gateway' + generateUUID();
}
//client
client = new Paho.MQTT.Client('ws://140.116.39.212:9200/', clientID.ID);