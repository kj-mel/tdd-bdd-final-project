# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Create a product and then try to read it"""
        product = ProductFactory()
        product.id = None

        product.create()
        self.assertIsNotNone(product.id)

        new_product = Product.find(product.id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_update_a_product(self):
        """It should update a product"""
        product = ProductFactory()
        product.id = None

        product.create()
        self.assertIsNotNone(product.id)

        product.description = "changing the description"
        product.update()

        products = Product.all()
        self.assertEqual(len(products), 1)

        changing_product = products[0]
        self.assertEqual(changing_product.id, product.id)
        self.assertEqual(changing_product.description, product.description)

    def test_delete_a_product(self):
        """It should delete a product"""
        product = ProductFactory()
        product.id = None

        product.create()
        self.assertIsNotNone(product.id)

        products = Product.all()
        self.assertEqual(len(products), 1)

        product.delete()

        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_list_all_products(self):
        """It should list all products"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()

        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_a_product_by_name(self):
        """It should find a product by name"""
        products = [ProductFactory() for _ in range(5)]
        for product in products:
            product.create()

        first_product = products[0]
        occurrencess = sum(1 if first_product.name == p.name else 0 for p in products)

        finding_products = Product.find_by_name(first_product.name)
        self.assertEqual(finding_products.count(), occurrencess)
        for product in finding_products:
            self.assertEqual(product.name, first_product.name)

    def test_find_a_product_by_availability(self):
        """It should find a product by availability"""
        products = [ProductFactory() for _ in range(10)]
        for product in products:
            product.create()

        availability = products[0].available
        count = sum(1 if p.available == availability else 0 for p in products)
        found = Product.find_by_availability(availability)
        self.assertEqual(found.count(), count)

        for product in found:
            self.assertEqual(product.available, availability)

    def test_find_a_product_by_category(self):
        """It should find a product by category"""
        products = [ProductFactory() for _ in range(10)]
        for product in products:
            product.create()

        category = products[0].category
        count = sum(1 if p.category == category else 0 for p in products)

        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)

        for product in found:
            self.assertEqual(product.category, category)

    def test_update_a_product_with_none_id(self):
        """It should raise an error when try to update a product without id"""
        product = ProductFactory()
        product.create()

        self.assertIsNotNone(product.id)

        product.name = "Zapatos"
        product.id = None

        self.assertRaises(DataValidationError, product.update)

    def test_raise_errors_with_invalid_data_in_deserialize_product(self):
        """It should raise an error when try to deserialize a product with invalid data"""
        product = Product()

        product_dict_valid = {
            "name": "Shirt",
            "description": "una camisa polo",
            "price": 23.32,
            "available": False,
            "category": "CLOTHS"
        }

        # Invalid available
        invalid_prod = product_dict_valid
        invalid_prod['available'] = "False"

        self.assertRaises(DataValidationError, product.deserialize, invalid_prod)

        # invalid category
        invalid_prod = product_dict_valid
        invalid_prod["category"] = "INVALID_CATEGORY_NAME"
        self.assertRaises(DataValidationError, product.deserialize, invalid_prod)

        # invalid type of dict
        self.assertRaises(DataValidationError, product.deserialize, {})

        # invalid data
        self.assertRaises(DataValidationError, product.deserialize, [])

        invalid_data = {
            "name": "Stethoscope",
            "description": "High-quality medical stethoscope",
            "price": "149.99",
            "available": True,
            "category": "INVALID_CATEGORY_NAME"  # This will trigger the AttributeError in getattr()
        }

        self.assertRaises(DataValidationError, product.deserialize, invalid_data)

    def test_find_a_product_by_price(self):
        """It should find a product by price"""
        products = [ProductFactory() for _ in range(10)]
        for product in products:
            product.create()

        price = products[0].price
        count = sum(1 if p.price == price else 0 for p in products)

        found = Product.find_by_price(price)
        self.assertEqual(found.count(), count)

        for product in found:
            self.assertEqual(product.price, price)

        found = Product.find_by_price("32.3")
