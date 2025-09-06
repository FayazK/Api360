import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.services.pdf_service import generate_pdf


class TestGeneratePdf:
    """Test PDF generation functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_simple_pdf(self):
        """Test generating PDF from simple HTML."""
        html_content = "<html><body><h1>Test PDF</h1><p>This is a test.</p></body></html>"
        
        with patch('app.services.pdf_service.HTML') as mock_html:
            # Mock the HTML class and its write_pdf method
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            
            # Mock write_pdf to write some bytes to the buffer
            def mock_write_pdf(buffer):
                buffer.write(b"fake pdf content")
            
            mock_html_instance.write_pdf.side_effect = mock_write_pdf
            
            result = await generate_pdf(html_content)
            
            assert result == b"fake pdf content"
            mock_html.assert_called_once_with(string=html_content)
            mock_html_instance.write_pdf.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_pdf_with_complex_html(self):
        """Test generating PDF from complex HTML with styles."""
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                h1 { color: blue; }
                .highlight { background-color: yellow; }
            </style>
        </head>
        <body>
            <h1>Complex PDF Test</h1>
            <p class="highlight">This is highlighted text.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
        </html>
        """
        
        with patch('app.services.pdf_service.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            
            def mock_write_pdf(buffer):
                buffer.write(b"complex pdf content")
            
            mock_html_instance.write_pdf.side_effect = mock_write_pdf
            
            result = await generate_pdf(html_content)
            
            assert result == b"complex pdf content"
            mock_html.assert_called_once_with(string=html_content)
    
    @pytest.mark.asyncio
    async def test_generate_pdf_empty_content(self):
        """Test generating PDF from empty HTML."""
        html_content = ""
        
        with patch('app.services.pdf_service.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            
            def mock_write_pdf(buffer):
                buffer.write(b"empty pdf")
            
            mock_html_instance.write_pdf.side_effect = mock_write_pdf
            
            result = await generate_pdf(html_content)
            
            assert result == b"empty pdf"
            mock_html.assert_called_once_with(string=html_content)
    
    @pytest.mark.asyncio
    async def test_generate_pdf_malformed_html(self):
        """Test generating PDF from malformed HTML."""
        html_content = "<html><body><h1>Unclosed header<p>Unclosed paragraph</body></html>"
        
        with patch('app.services.pdf_service.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            
            def mock_write_pdf(buffer):
                buffer.write(b"malformed pdf content")
            
            mock_html_instance.write_pdf.side_effect = mock_write_pdf
            
            result = await generate_pdf(html_content)
            
            assert result == b"malformed pdf content"
            mock_html.assert_called_once_with(string=html_content)
    
    @pytest.mark.asyncio
    async def test_generate_pdf_weasyprint_error(self):
        """Test handling of WeasyPrint errors."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        
        with patch('app.services.pdf_service.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.side_effect = Exception("WeasyPrint error")
            
            with pytest.raises(Exception, match="WeasyPrint error"):
                await generate_pdf(html_content)
    
    @pytest.mark.asyncio
    async def test_buffer_handling(self):
        """Test that BytesIO buffer is properly handled."""
        html_content = "<html><body>Test</body></html>"
        
        with patch('app.services.pdf_service.HTML') as mock_html, \
             patch('app.services.pdf_service.BytesIO') as mock_bytesio:
            
            # Create a mock buffer
            mock_buffer = Mock()
            mock_buffer.getvalue.return_value = b"test pdf content"
            mock_bytesio.return_value = mock_buffer
            
            # Mock HTML instance
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            
            result = await generate_pdf(html_content)
            
            # Verify buffer operations
            mock_bytesio.assert_called_once()
            mock_html_instance.write_pdf.assert_called_once_with(mock_buffer)
            mock_buffer.getvalue.assert_called_once()
            mock_buffer.close.assert_called_once()
            
            assert result == b"test pdf content"