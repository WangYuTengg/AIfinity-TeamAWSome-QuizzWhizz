async function downloader(url) {

    const {By, Builder, Browser, until} = require('selenium-webdriver');
    const chrome = require('selenium-webdriver/chrome');
    var webdriver = require('selenium-webdriver')

    //launch browser
    const driver = await new Builder().forBrowser("chrome").build();

    //nagivate to application
    await driver.get("https://en1.onlinevideoconverter.pro/18/youtube-video-downloader")
    var textBox = await driver.findElement(By.id('texturl'));
    var submitButton = await driver.findElement(By.id('convert1'))
    await textBox.sendKeys(url);
    await submitButton.click();

    var downloadLocator = await driver.wait(until.elementLocated(By.id('download-720-MP4')), 10000)
    await downloadLocator.click()
    //

} 

export default downloader