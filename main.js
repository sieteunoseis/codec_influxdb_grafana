// If using Self-Signed CERT on Endpoints do this...
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const { TpEndpoint } = require('cisco-tp-snapshots');
// If saving to local file system
const fs = require('fs');

const ce = new TpEndpoint({
	host: 'cisco_sx_20.us164.corpintra.net',
	username: 'admin',
	password: 'Trucks08!'
});

// Verify Endpoint has the Feature
ce.verifyTpEndpoint().then(enabled => {
	if(enabled) {
		return ce.getVideoInputs().then(inputs => {
			// [{sourceId: '1', type: 'inputType <camera|hdmi|etc>'}]
			return ce.takeSnapshot(inputs[0].sourceId).then(img => {
				// What to do with the Image ?
				fs.writeFile('./images/' + host + '.png', img, {encoding: 'base64'}, (e) => {})
				// If you want to Add it to an HTML <img>
				// img = 'data:image/jpeg;base64,' + img
				// <img src=img />
			})
		})
	}
})