#!/usr/bin/env python3
"""
Unit tests for PACER client code support.

Tests that the PacerSession correctly includes the client code
in authentication requests when provided.
"""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from juriscraper.pacer.http import PacerSession


class TestPacerClientCodeSupport(unittest.TestCase):
    """Test client code support in PacerSession."""

    def test_client_code_in_init(self):
        """Test that client code is stored during initialization."""
        session = PacerSession(
            username="testuser",
            password="testpass",
            client_code="TEST123"
        )
        
        self.assertEqual(session.client_code, "TEST123")
        self.assertEqual(session.username, "testuser")
        self.assertEqual(session.password, "testpass")

    def test_client_code_none_by_default(self):
        """Test that client code is None when not provided."""
        session = PacerSession(
            username="testuser",
            password="testpass"
        )
        
        self.assertIsNone(session.client_code)

    @patch('juriscraper.pacer.http.PacerSession._prepare_login_request')
    def test_client_code_included_in_login_request(self, mock_prepare_login):
        """Test that client code is included in the login request data."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nextGenCSO": "token",
            "loginResult": "0"  # Successful login
        }
        mock_prepare_login.return_value = mock_response
        
        session = PacerSession(
            username="testuser",
            password="testpass",
            client_code="CLIENT123"
        )
        
        # Call login
        session.login()
        
        # Verify that _prepare_login_request was called
        self.assertTrue(mock_prepare_login.called)
        
        # Get the call arguments
        call_args = mock_prepare_login.call_args
        
        # The data should be the second positional argument (after url)
        # or in kwargs as 'data'
        if len(call_args[0]) > 1:
            data_json = call_args[0][1]  # data parameter
        else:
            data_json = call_args[1]['data']
        
        # Parse the JSON data
        data = json.loads(data_json)
        
        # Verify client code is in the request
        self.assertIn("clientCode", data)
        self.assertEqual(data["clientCode"], "CLIENT123")
        self.assertEqual(data["loginId"], "testuser")
        self.assertEqual(data["password"], "testpass")
        self.assertEqual(data["redactFlag"], "1")

    @patch('juriscraper.pacer.http.PacerSession._prepare_login_request')
    def test_client_code_not_included_when_none(self, mock_prepare_login):
        """Test that client code is not included when it's None."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nextGenCSO": "token",
            "loginResult": "0"  # Successful login
        }
        mock_prepare_login.return_value = mock_response
        
        session = PacerSession(
            username="testuser",
            password="testpass",
            client_code=None
        )
        
        # Call login
        session.login()
        
        # Verify that _prepare_login_request was called
        self.assertTrue(mock_prepare_login.called)
        
        # Get the call arguments
        call_args = mock_prepare_login.call_args
        
        # The data should be the second positional argument (after url)
        # or in kwargs as 'data'
        if len(call_args[0]) > 1:
            data_json = call_args[0][1]  # data parameter
        else:
            data_json = call_args[1]['data']
        
        # Parse the JSON data
        data = json.loads(data_json)
        
        # Verify client code is NOT in the request
        self.assertNotIn("clientCode", data)
        self.assertEqual(data["loginId"], "testuser")
        self.assertEqual(data["password"], "testpass")
        self.assertEqual(data["redactFlag"], "1")

    @patch('juriscraper.pacer.http.PacerSession._prepare_login_request')
    def test_client_code_with_empty_string(self, mock_prepare_login):
        """Test that empty string client code is not included."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nextGenCSO": "token",
            "loginResult": "0"  # Successful login
        }
        mock_prepare_login.return_value = mock_response
        
        session = PacerSession(
            username="testuser",
            password="testpass",
            client_code=""
        )
        
        # Call login
        session.login()
        
        # Verify that _prepare_login_request was called
        self.assertTrue(mock_prepare_login.called)
        
        # Get the call arguments
        call_args = mock_prepare_login.call_args
        
        # The data should be the second positional argument (after url)
        # or in kwargs as 'data'
        if len(call_args[0]) > 1:
            data_json = call_args[0][1]  # data parameter
        else:
            data_json = call_args[1]['data']
        
        # Parse the JSON data
        data = json.loads(data_json)
        
        # Verify client code is NOT in the request (empty string is falsy)
        self.assertNotIn("clientCode", data)

    def test_client_code_parameter_documentation(self):
        """Test that the client_code parameter is documented in __init__."""
        # Check that the parameter is in the function signature
        import inspect
        sig = inspect.signature(PacerSession.__init__)
        params = sig.parameters
        
        self.assertIn('client_code', params)
        self.assertEqual(params['client_code'].default, None)
        
        # Check that it's documented in the docstring
        docstring = PacerSession.__init__.__doc__
        self.assertIsNotNone(docstring)
        self.assertIn('client_code', docstring.lower())


class TestPacerClientCodeIntegration(unittest.TestCase):
    """Integration tests for client code functionality."""

    def test_session_creation_with_all_params(self):
        """Test creating a session with all parameters including client code."""
        session = PacerSession(
            username="user@example.com",
            password="SecurePass123!",
            client_code="ORG-12345"
        )
        
        self.assertEqual(session.username, "user@example.com")
        self.assertEqual(session.password, "SecurePass123!")
        self.assertEqual(session.client_code, "ORG-12345")
        self.assertFalse(session.get_acms_tokens)

    def test_session_creation_with_client_code_and_acms(self):
        """Test creating a session with both client code and ACMS tokens enabled."""
        session = PacerSession(
            username="user@example.com",
            password="SecurePass123!",
            client_code="ORG-12345",
            get_acms_tokens=True
        )
        
        self.assertEqual(session.client_code, "ORG-12345")
        self.assertTrue(session.get_acms_tokens)


if __name__ == "__main__":
    unittest.main()

