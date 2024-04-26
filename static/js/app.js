document.addEventListener('DOMContentLoaded', function() {
    var socket = io();
    var desktopImg = document.getElementById('desktop');

    // Recibir y mostrar la imagen del escritorio
    socket.on('screen_capture', function(data) {
        desktopImg.src = 'data:image/jpeg;base64,' + data.image;
    });

    // Calcular las coordenadas ajustadas y enviar el evento de clic del ratón
    function sendMouseClick(event, button) {
        var rect = desktopImg.getBoundingClientRect();
        var scaleX = desktopImg.naturalWidth / rect.width;
        var scaleY = desktopImg.naturalHeight / rect.height;

        var x = (event.clientX - rect.left) * scaleX;
        var y = (event.clientY - rect.top) * scaleY;

        socket.emit('mouse_click', {x: Math.round(x), y: Math.round(y), button: button});
    }

    // Eventos de clic del ratón
    desktopImg.addEventListener('click', function(event) {
        sendMouseClick(event, 'left');
    });

    desktopImg.addEventListener('contextmenu', function(event) {
        event.preventDefault();
        sendMouseClick(event, 'right');
        return false; // Evitar el menú contextual del navegador
    });

    // Enviar eventos de movimiento del ratón
    desktopImg.addEventListener('mousemove', function(event) {
        var rect = desktopImg.getBoundingClientRect();
        var scaleX = desktopImg.naturalWidth / rect.width;
        var scaleY = desktopImg.naturalHeight / rect.height;

        var x = (event.clientX - rect.left) * scaleX;
        var y = (event.clientY - rect.top) * scaleY;

        socket.emit('mouse_move', {x: Math.round(x), y: Math.round(y)});
    });

    // Enviar eventos de scroll del ratón
    desktopImg.addEventListener('wheel', function(event) {
        socket.emit('mouse_scroll', {deltaY: event.deltaY});
        event.preventDefault(); // Evitar el scroll de la página
    });

    // Enviar eventos de teclado
document.addEventListener('keydown', function(event) {
    // Verificar si la combinación de teclas incluye Control

    if (event.ctrlKey) {
    switch (event.key) {
        case 'x':  // Control + X
            socket.emit('combination_key_press', {
                combination: 'ctrl+x',
            });
            event.preventDefault();  // Evitar que el navegador corte el texto
            break;
        case 'c':  // Control + C
            socket.emit('combination_key_press', {
                combination: 'ctrl+c',
            });
            event.preventDefault();  // Evitar que el navegador copie el texto
            break;
        case 'v':  // Control + V
            socket.emit('combination_key_press', {
                combination: 'ctrl+v',
            });
            event.preventDefault();  // Evitar que el navegador pegue texto
            break;
        case 'z':  // Control + Z
            socket.emit('combination_key_press', {
                combination: 'ctrl+z',
            });
            event.preventDefault();  // Evitar que el navegador deshaga
            break;
        case 'y':  // Control + Y
            socket.emit('combination_key_press', {
                combination: 'ctrl+y',
            });
            event.preventDefault();  // Evitar que el navegador rehaga
            break;
        case 'a':  // Control + A
            socket.emit('combination_key_press', {
                combination: 'ctrl+a',
            });
            event.preventDefault();  // Evitar que el navegador seleccione todo
            break;
        case 's':  // Control + S
            socket.emit('combination_key_press', {
                combination: 'ctrl+s',
            });
            event.preventDefault();  // Evitar que el navegador guarde la página
            break;
        case 'p':  // Control + P
            socket.emit('combination_key_press', {
                combination: 'ctrl+p',
            });
            event.preventDefault();  // Evitar que el navegador imprima la página
            break;
        case 't':  // Control + T
            socket.emit('combination_key_press', {
                combination: 'ctrl+t',
            });
            event.preventDefault();  // Evitar que el navegador abra una nueva pestaña
            break;
        case 'n':  // Control + N
            socket.emit('combination_key_press', {
                combination: 'ctrl+n',
            });
            event.preventDefault();  // Evitar que el navegador abra una nueva ventana
            break;
        case 'f':  // Control + F
            socket.emit('combination_key_press', {
                combination: 'ctrl+f',
            });
            event.preventDefault();  // Evitar que el navegador abra el cuadro de búsqueda
            break;
        // Agregar más casos si es necesario
    }
} else {
    let keyToSend = '';
    switch(event.key) {
        case 'ArrowUp':
            keyToSend = 'up';
            break;
        case 'ArrowDown':
            keyToSend = 'down';
            break;
        case 'ArrowLeft':
            keyToSend = 'left';
            break;
        case 'ArrowRight':
            keyToSend = 'right';
            break;
        default:
            keyToSend = event.key; // Envía la tecla original si no es una de las flechas
    }

    // Emitir el evento con la nueva clave
    socket.emit('key_press', {
        key: keyToSend
    });
        event.preventDefault();  // Evitar que el navegador abra el cuadro de búsqueda

    }
});
});
