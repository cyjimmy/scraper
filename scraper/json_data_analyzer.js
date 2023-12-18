data = require('./scraped_data/car_listings.json')

counter = 0
for (let item in data) {
    if (data[item].price !== null) {
        counter++
    }
}
console.log(counter)