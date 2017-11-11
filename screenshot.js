const bluebird = require("bluebird");
const puppeteer = require("puppeteer");
const ms = require("ms");

const DELAY = ms("10s");
const INTERVAL = ms("30m");
async function main() {
    const browser = await puppeteer.launch();
    try {
        while(true) {
            const page = await browser.newPage();
            try {
                page.setViewport({width: 1400, height: 730});
                await page.goto("http://localhost:5000");
                await bluebird.delay(DELAY);
                await page.screenshot({
                    path: "static/share.jpeg",
                    type: "jpeg",
                    quality: 60,
                    clip: {
                        x: 50,
                        y: 50,
                        width: 1200,
                        height: 630
                    }
                });
            } finally {
                await page.close();
                await bluebird.delay(INTERVAL);
            }
        }
    } finally {
        await browser.close();
    }
}

main()
.then(() => {
    process.exit(0);
})
.catch((err) => {
    console.error(err.stack);
    process.exit(1);
});
